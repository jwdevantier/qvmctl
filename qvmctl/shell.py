import subprocess
from typing import Union, List
from qvmctl.utils import colors


def sh(
    args: Union[str, List[str]], echo=True, check=True, desc=None, **kwargs
) -> subprocess.CompletedProcess:
    if desc:
        print(f"{colors.B_MAGENTA} {colors.B_GREY}{desc}{colors.CLR}")
    if echo:
        fmt = args if isinstance(args, str) else " ".join(args)
        print(f"{colors.B_GREEN}> {colors.B_WHITE}{fmt}{colors.CLR}")

    kwargs["shell"] = True if isinstance(args, str) else False
    kwargs["check"] = check
    return subprocess.run(args, **kwargs)
