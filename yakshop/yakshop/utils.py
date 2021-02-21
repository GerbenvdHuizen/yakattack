import os
from typing import Any, Callable, Optional


def get_env_var(name: str, default: Any = None, cast_func: Callable[[str], Any] = lambda a: a) -> Optional[Any]:
    value = os.environ.get(name)
    if not value or len(value) == 0:
        return default
    else:
        return cast_func(value)


def env_to_bool(value: Optional[str]):
    return False if not value or value == '0' or value == 'False' or value == 'false' else True
