from abc import ABC, abstractmethod

class Executor(ABC):
    @abstractmethod
    def execute_test_cases(self):
        """
        Abstract method to execute test cases.
        Subclasses must provide an implementation.
        """
        pass