from typing import Any

class JsonDict(dict):  # type: ignore[type-arg]
    """general json object that allows attributes to be bound to and also behaves like a dict"""

    def __getattr__(self, attr: Any) -> Any:
        return self.get(attr)

    def __setattr__(self, attr: Any, value: Any) -> None:
        self[attr] = value