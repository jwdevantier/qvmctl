import importlib
from typing import Callable


def resolv_hook(hook_str: str) -> Callable:
    hook_elems = hook_str.split(":")
    if not len(hook_elems) == 2:
        raise ValueError("expected a hook of the form 'path.to.module:hook_fn'")
    hook_mod_path, hook_fn = hook_elems
    mod = importlib.import_module(hook_mod_path)
    if not hasattr(mod, hook_fn):
        raise ValueError(f"'{hook_fn}' in module {mod} does not exist")
    fn = getattr(mod, hook_fn)
    if not callable(fn):
        raise ValueError(f"'{hook_fn}' in module {mod} is not a callable")
    return fn
