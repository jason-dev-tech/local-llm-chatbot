from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Tool:
    name: str
    function: Callable[..., str]

    def run(self, *args, **kwargs) -> str:
        return self.function(*args, **kwargs)
