import json
import random
import numpy as np
from mthree.utils import vector_to_quasiprobs, counts_to_vector
from qiskit import QuantumCircuit

from QOPS.abstract_classes import Executor


class Circuit_Tester:
    def __init__(self,CUT:QuantumCircuit, CPS:dict, executor:Executor, threshold:float=None,budget:int=100,mode:str="single",batch:int=None,output:str=None):
        """
        :param CUT: A qiskit circuit without measurements
        :param CPS: A compact program specification with format {PauliString:counts}
        :param executor: An object of executor class defining function "execute_test_cases"
        :param threshold: Threshold for considering a test case passsed or failed, if defined the code will stop on
               max budget or if a threshold test case is found
        :param budget: Total number of testcases to evaluate
        :param mode: 'single' or 'batch'
        :param batch: if mode is batch then this parameter defines the batch size to run the test cases
        """
        self.compact_program_specification = None
        self.CUT = CUT
        self.budget = budget
        self.threshold = threshold
        self.set_applicable_families_Z(CPS)
        self.executor = executor
        if mode == "single" or mode == "batch":
            self.mode = mode
        else:
            raise ValueError("Mode must be 'single' or 'batch'")

        if mode == "batch" and batch is None:
            raise ValueError("batch size must be specified if mode is batch")

        self.batch = batch
        self.output = output

    def set_applicable_families_Z(self,compact_program_specification:dict):
        """
        :param compact_program_specification: dict of paulistring with their measurement results
        """
        self.compact_program_specification = compact_program_specification
        self.applicable_families = []
        zfam = "Z"*(2**self.CUT.num_qubits)
        for key,value in compact_program_specification.items():
            if key in zfam:
                self.applicable_families.append((0, value))

    def get_random_Z_family(self, qubits):
        N = 2 ** qubits
        total = range(1, random.randint(2, 32))
        values = [random.randint(a=1, b=N - 1) for _ in total]
        f = []
        for i in values:
            b = bin(i)[2:]
            b = b.zfill(qubits)
            b = b.replace("1", "Z").replace("0", "I")
            f.append(b)
        return f

    def random_test_case_Z(self):
        pauli_dict = {}
        fam = random.choice(self.applicable_families)
        selected_pauli = self.get_random_Z_family(self.CUT.num_qubits)
        for s in selected_pauli:
            pauli_dict[s] = np.random.random()
        return {"test_case":pauli_dict,"family_index":fam[0],"M":fam[-1]}


    def get_test_case_theoretics_Z(self,test_case:dict):
        return {"test_case": test_case["test_case"], "M": test_case["M"]}

    def get_theoretical_exp_from_testcase(self, test_case:dict):

        def pauli_expectation_from_counts(counts, pauli_string):
            pauli_string = pauli_string.upper()
            total_counts = sum(counts.values())
            exp_val = 0.0
            for bitstring, count in counts.items():
                v = 1
                for i, p in enumerate(pauli_string):
                    if p == 'Z':
                        v *= 1 if bitstring[i] == '0' else -1
                exp_val += v * count
            return exp_val / total_counts

        # Compute expectation value of the Hamiltonian
        counts = test_case["M"]
        expectation = sum(
            coeff * pauli_expectation_from_counts(counts, pauli_str)
            for pauli_str, coeff in test_case['test_case'].items()
        )
        return expectation

    def get_theoretical_exp_from_test_case_M3(self, test_case:dict):

        counts = test_case["M"]
        quasi = vector_to_quasiprobs(counts_to_vector(counts),counts)
        expectation = sum([v*quasi.expval(exp_ops=x) for x,v in test_case["test_case"].items()])
        return expectation


    def run_randomsearch(self):
        if self.mode == 'single':
            record = {"Max Diff":0, "Max Diff. Test Case": {}, "history":[]}
            for i in range(self.budget):
                testcase = self.random_test_case_Z()
                test_case = self.get_test_case_theoretics_Z(testcase)
                exp = self.get_theoretical_exp_from_test_case_M3(test_case)
                obs = self.executor.execute_test_cases(self.CUT, [test_case["test_case"]])[0]
                if abs(exp - obs)>record["Max Diff"]:
                    record["Max Diff"] = abs(exp - obs)
                    record["Max Diff. Test Case"] = test_case["test_case"]
                record["history"].append({"Diff":abs(exp - obs),"Test_Case":test_case["test_case"]})

                if self.threshold is not None:
                    if record["Max Diff"] >= self.threshold:
                        print("threshold reached")
                        return record
            print("max budget reached")
            if self.output:
                with open(self.output, "w") as f:
                    json.dump(record,f)
            return record

        else:
            record = {"Max Diff": 0, "Max Diff. Test Case": {}, "history": []}
            total_run = 0
            while total_run < self.budget:
                this_batch_size = min(self.batch, self.budget - total_run)

                batch_raw_cases = []
                batch_full_cases = []
                for _ in range(this_batch_size):
                    testcase = self.random_test_case_Z()
                    test_case = self.get_test_case_theoretics_Z(testcase)
                    batch_raw_cases.append(test_case["test_case"])
                    batch_full_cases.append(test_case)

                exps = [self.get_theoretical_exp_from_test_case_M3(tc) for tc in batch_full_cases]
                obs_list = self.executor.execute_test_cases(self.CUT, batch_raw_cases)

                for exp, obs, raw_case in zip(exps, obs_list, batch_raw_cases):
                    diff = abs(exp - obs)
                    if diff > record["Max Diff"]:
                        record["Max Diff"] = diff
                        record["Max Diff. Test Case"] = raw_case
                    record["history"].append({"Diff": diff, "Test_Case": raw_case})

                    if self.threshold is not None:
                        if record["Max Diff"] >= self.threshold:
                            print("threshold reached")
                            return record

                total_run += this_batch_size
            print("max budget reached")
            if self.output:
                with open(self.output, "w") as f:
                    json.dump(record,f)
            return record