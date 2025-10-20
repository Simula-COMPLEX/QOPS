# QOPS

Quantum Program Testing Through Commuting Pauli Strings

## Key Features
- Random-search test generation tailored to Z-family Pauli observables.
- Backend abstraction that lets you plug in custom executors; ships with a Qiskit-based AER GPU/CPU ideal simulation executor.
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
You can drive the tester directly in Python to integrate it into notebooks or pipelines:
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

- **Large circuits**: Increase `--budget` gradually; expectation estimation scales with the number of sampled Pauli strings.
- **Deterministic runs**: Wrap `random.seed()` and `numpy.random.seed()` before calling `Circuit_Tester` if reproducibility matters.
