from abc import ABC, abstractmethod

class Issue(ABC):
    id: str
    description: str
    severity: str
    fix_description: str

    @abstractmethod
    def apply_fix(self, input_path, output_path):
        pass
