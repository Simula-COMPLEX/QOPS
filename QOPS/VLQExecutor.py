from qaas import QBackend, QProvider
from py4lexis.session import LexisSession
from QOPS.abstract_classes import Executor
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp


class VLQ_Executor(Executor):
    def __init__(self):
        self.session = LexisSession()
        self.lexis_project = "vlq_demo_project"
        self.resource_name = "qaas_user"
        self.token = self.session.get_access_token()
        self.provider = QProvider(self.token, self.lexis_project, self.resource_name)
        self.shots = 10000
        self.backend:QBackend = self.provider.get_backend()

    def expectation_from_VLQ(self, qc: QuantumCircuit, H: SparsePauliOp) -> float:
        """
        Compute ⟨H⟩ = ⟨ψ|H|ψ⟩ using Qbackend,
        assuming H has only I and Z Paulis.
        """
        # 1. Make a copy of the circuit and add measurements in the Z basis
        qc_meas = qc.copy()
        qc_meas.measure_all()

        # 2. Run
        transpiled_qc = self.backend.transpile_to_IQM(qc_meas)
        counts = self.backend.run(transpiled_qc,
                             shots=self.shots).result().get_counts()
        
        # 3. Normalize counts into probabilities
        probs = {bitstr: c / self.shots for bitstr, c in counts.items()}

        # 4. Prepare Z-term list
        terms = []
        for pstr, coeff in zip(H.paulis.to_labels(), H.coeffs):
            # Reverse since Qiskit bit order is little-endian (rightmost = qubit 0)
            z_qubits = [q for q, ch in enumerate(reversed(pstr)) if ch == 'Z']
            terms.append((tuple(z_qubits), complex(coeff)))

        # 5. Compute expectation ⟨H⟩ = Σ_bitstring p(bitstring) * ⟨H⟩_bitstring
        exp_H = 0.0 + 0.0j
        for bitstr, p in probs.items():
            eig_sum = 0.0 + 0.0j
            # convert bitstring (leftmost = most significant bit)
            bits = bitstr[::-1]  # reverse for qubit index alignment
            for z_qubits, coeff in terms:
                eig = 1
                for q in z_qubits:
                    eig *= (1 if bits[q] == '0' else -1)
                eig_sum += coeff * eig
            exp_H += p * eig_sum

        return float(np.real_if_close(exp_H))

    def execute_test_cases(self, CUT:QuantumCircuit, test_cases: list[dict]):
        results = []
        for test_case in test_cases:
            sp = [(k, v) for k, v in test_case.items()]
            M1 = SparsePauliOp.from_list(sp)
            exp = self.expectation_from_VLQ(CUT, M1)
            results.append(exp)
        
        return results