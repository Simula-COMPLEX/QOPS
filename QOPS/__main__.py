import json
from qiskit import qasm3
from QOPS.Tester import Circuit_Tester
from QOPS.QiskitExecutor import Qiskit_Executor
import argparse
# if __name__ == '__main__':
#     CUT = test_data.get_random_circuit(5)
#     CPS = test_data.get_compact_program_specification_Z(CUT,shots=10000)
#
#     executor = Qiskit_Executor()
#
#     CTS = Circuit_Tester(CUT, CPS, executor, threshold=0.1,budget=10,mode="batch",batch=5)
#     print(CTS.run_randomsearch())

def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run QOPS with specified parameters.\n"
            "Example:\n"
            "  python circuit_cli.py --qasmfile my_circuit.qasm "
            "--cpsfile cps.json --threshold 0.1 --budget 10 "
            "--mode batch --batch 5"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # CLI arguments
    parser.add_argument(
        "--qasmfile", "-q",
        type=str,
        required=True,
        help="Path to the OpenQASM2 file describing the circuit-under-test without measurements."
    )

    parser.add_argument(
        "--cpsfile", "-c",
        type=str,
        required=True,
        help="Path to the CPS JSON file containing Compact Program specification."
    )

    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=None,
        help="Threshold value for test-case evaluation (default: None)."
    )

    parser.add_argument(
        "--budget", "-b",
        type=int,
        default=100,
        help="Maximum number of test cases to run (default: 100)."
    )

    parser.add_argument(
        "--mode", "-m",
        type=str,
        choices=["single", "batch"],
        default="single",
        help="Mode of execution: 'single' runs tests one by one; "
             "'batch' runs tests in batches (default: single)."
    )

    parser.add_argument(
        "--batch", "-B",
        type=int,
        default=5,
        help="Batch size for batch mode (default: 5 — ignored in single mode)."
    )

    parser.add_argument(
        "--output", "-O",
        type=str,
        default=None,
        help="Output file path (default: None — if none will only print Max diff result)."
    )

    args = parser.parse_args()


    CUT = qasm3.load(str(args.qasmfile))
    with open(str(args.cpsfile), "r") as file:
        CPS = json.load(file)
    executor = Qiskit_Executor()
    # Create and run Circuit_Tester
    CTS = Circuit_Tester(
        CUT,
        CPS,
        executor,
        threshold=args.threshold,
        budget=args.budget,
        mode=args.mode,
        batch=args.batch,
        output=args.output,
    )

    result = CTS.run_randomsearch()
    print(result["Max Diff"])
    print(result["Max Diff. Test Case"])


if __name__ == "__main__":
    main()