# QOPS

Quantum Program Testing Through Commuting Pauli Strings

## Key Features
- Random-search test generation tailored to Z-family Pauli observables.
- Backend abstraction that lets you plug in custom executors; ships with a Qiskit-based AER GPU/CPU ideal simulation executor and VLQ Quantum Computer Executor.
- Batch and single-test execution modes with optional early stopping once a deviation threshold is exceeded.

## Installation
- **Prerequisites**: Python 3.11+, and (optionally) NVIDIA CUDA 11 support if you want to run the Aer GPU simulator bundled with the default executor.
- **Install in a virtual environment (recommended)**:
  ```bash
  python -m venv .venv
  source .venv/bin/activate
  python -m pip install --upgrade pip
  python -m pip install .
  ```

## Usage
### You can run QOPS in two modes: CLI and Module Library
You need two inputs to run QOPS:
1. **Circuit Under Test (CUT)**: An OpenQASM 3 file without measurements.
2. **Compact Program Specification (CPS)**: A JSON document mapping a single Pauli string to measurement counts (For more details read the original [paper](https://dl.acm.org/doi/abs/10.1145/3691620.3695275)). An Example of CPS is shown below:

```Json
{"ZZZZZ": {"11001": 348, "11011": 345, "01100": 262, "10010": 273, "10000": 290, "00011": 51, "11101": 761, "01011": 300, "00111": 160, "10011": 72, "10110": 620, "01101": 740, "01111": 786, "01110": 231, "11100": 257, "00100": 624, "00110": 642, "11111": 718, "11110": 244, "00000": 246, "10111": 136, "01000": 97, "10100": 587, "11010": 123, "01001": 301, "00010": 231, "01010": 89, "00101": 116, "00001": 55, "11000": 102, "10101": 123, "10001": 70}}
```

## Command-Line Usage
The package exposes a CLI via `python -m QOPS`:
```bash
python -m QOPS \
  --qasmfile testcircuit.qasm \
  --cpsfile testcps.json \
  --budget 100 \
  --mode batch \
  --batch 10 \
  --threshold 0.1 \
  --output report.json
```

- `--qasmfile` / `--cpsfile`: Required paths to the CUT and CPS artifacts.
- `--budget`: Maximum number of random test cases to evaluate (default 100).
- `--mode`: `single` runs one test at a time; `batch` runs tests in batches if the executor allows (Default QiskiExecutor can run in batches).
- `--batch`: Size of each batch when `--mode batch` is selected.
- `--threshold`: Optional early-stop condition based on absolute deviation.
- `--output`: Writes the full search history to JSON; otherwise only console output is produced.

The CLI prints two lines: the maximum observed absolute deviation (`Max Diff`) and the Test case that triggered it. When `--output` is set, the file also includes every tested Pauli string and its individual deviation.

## Python API
You can drive the tester directly in Python to integrate it into notebooks or pipelines that utilize HPC or real quantum computers:
## Ex3 and Sigma Execution:
On Ex3 the QOPS can run as the cli mode with the above command or it can be used in the python scripts. An example code to run on Ex3 using Qiskit is given below:
```python
from QOPS.Tester import Circuit_Tester
from QOPS.QiskitExecutor import Qiskit_Executor
from qiskit import qasm3
import json

cut = qasm3.load("testcircuit.qasm") # or you can create your own circuit

with open("testcps.json", "r") as f: # You can create your own cps python dict object 
    cps = json.load(f)               #

executor = Qiskit_Executor()         # Default qiskit executor for ideal simulations
ct = Circuit_Tester(
    CUT=cut,
    CPS=cps,
    executor=executor,
    threshold=0.05,
    budget=50,
    mode="single",
    output=None,
)

result = ct.run_randomsearch()
print(result["Max Diff"], result["Max Diff. Test Case"])
```
The script can be run with slurm with the following example:
```python
#!/bin/bash
#SBATCH -p hgx2q,dgx2q
#SBATCH --job-name=qops
#SBATCH --gres=gpu:2          # number of gpus to use
#SBATCH --time 10-00:00:00    # time (D-HH:MM:SS)
module purge
module use /cm/shared/ex3-modules/latest/modulefiles
module load slurm/slurm/21.08.8
module load cuda11.8/toolkit/11.8.0
module load QOPS              # load the qops module from the available modules in ex3
srun mmpirun -np 2 python yourscript.py # here -np is the number of gpus available for
                                        # gpu execution and number of cpu nodes for cpu
                                        # execution
```

Instantiate your own executor by subclassing `QOPS.abstract_classes.Executor` and implementing `execute_test_cases(CUT, test_cases)` to hook the tester into custom hardware or simulators.

### Custom Executor Example
The executor interface lets you integrate any backend that can return expectation values for commuting Pauli strings. The example below sketches a lightweight CPU-only executor that uses Qiskit's built-in statevector simulator without invoking IBM Runtime sessions:

```python
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import SparsePauliOp, Statevector

from QOPS.abstract_classes import Executor


class SimpleStatevectorExecutor(Executor):
    def execute_test_cases(self, CUT: QuantumCircuit, test_cases: list[dict]) -> list[float]:
        # Transpile once per batch to match the simulator target.
        transpiled = transpile(CUT, optimization_level=1)
        statevec = Statevector.from_instruction(transpiled)

        results = []
        for pauli_dict in test_cases:
            pauli_op = SparsePauliOp.from_list(list(pauli_dict.items()))
            expectation = statevec.expectation_value(pauli_op).real
            results.append(expectation)
        return results


# Usage with the tester
from QOPS.Tester import Circuit_Tester
from qiskit import qasm3
import json

cut = qasm3.load("example_cut.qasm")
with open("example_cps.json") as f:
    cps = json.load(f)

executor = SimpleStatevectorExecutor()
tester = Circuit_Tester(cut, cps, executor, budget=25)
print(tester.run_randomsearch()["Max Diff"])
```

Swap the implementation body with calls to proprietary hardware, async job managers, or other simulators as needed—as long as `execute_test_cases` returns expectation values aligned with each Pauli dictionary it receives, QOPS will consume the results.

## VLQ Execution:
QOPS can be easily integrated and executed on VLQ using their Qaas package and creating a custom executor. An example executor that uses Qaas is provided in the QOPS module and also shown below:

```python
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
```

Using the custom VLQ executor with `execute_test_cases` function defined we can run QOPS on VLQ as follows:
```python
# Usage with the tester
from QOPS.Tester import Circuit_Tester
from qiskit import qasm3
import json

cut = qasm3.load("example_cut.qasm")
with open("example_cps.json") as f:
    cps = json.load(f)

executor = VLQ_Executor()               # VLQ execution logic in custom executor
tester = Circuit_Tester(cut, cps, executor, budget=25)
print(tester.run_randomsearch()["Max Diff"])
```

- **Large circuits**: Increase `--budget` gradually; expectation estimation scales with the number of sampled Pauli strings.
- **Deterministic runs**: Wrap `random.seed()` and `numpy.random.seed()` before calling `Circuit_Tester` if reproducibility matters.