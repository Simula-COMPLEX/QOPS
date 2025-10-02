import json

from qiskit import QuantumCircuit, generate_preset_pass_manager, qasm3
from qiskit.circuit.random import random_circuit
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime import Session, SamplerV2 as Sampler


def get_compact_program_specification_Z(circuit:QuantumCircuit,shots=4000, simulator_type='statevector'):
    try:
        aer_sim = AerSimulator(method="statevector", device='GPU', blocking_enable=True,
                                    batched_shots_gpu=True)
    except:
        aer_sim = AerSimulator(method="statevector", device='CPU', blocking_enable=True,
                                    batched_shots_gpu=True)

    pass_manager = generate_preset_pass_manager(backend=aer_sim, optimization_level=3)
    circuits = []
    pauli_string_list = []
    pauli = "Z"*(circuit.num_qubits)
    qc = QuantumCircuit(circuit.num_qubits, circuit.num_qubits)
    qc.compose(circuit,inplace=True)
    qc.measure(range(circuit.num_qubits), range(circuit.num_qubits))
    circuits.append(qc)
    pauli_string_list.append(pauli)

    isa_qc = pass_manager.run(circuits)
    with Session(backend=aer_sim) as session:
        sampler = Sampler(mode=session)
        results = sampler.run(isa_qc, shots=shots).result()
    counts = {}

    for paulistring, result in zip(pauli_string_list, results):
        counts[paulistring] = result.data.c.get_counts()
    return counts

def get_random_circuit(qubits:int):
    circuit = random_circuit(qubits,4,2,seed=42)
    return circuit

def mutation(circuit):
    m1 = circuit.copy()
    m1.ry(0.1,m1.num_qubits - 1)
    return m1


if __name__ == '__main__':
    CUT = get_random_circuit(5)
    CPS = get_compact_program_specification_Z(CUT,shots=10000)
    with open("testcircuit.qasm", "w") as file:
        qasm3.dump(CUT,file)
    with open("testcps.json","w") as file:
        json.dump(CPS,file)