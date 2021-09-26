from qvmctl.utils import colors
import traceback
import sys
from typing import Any, Dict


def pp_exc():
    typ, val, tb = sys.exc_info()
    if typ is None and val is None and tb is None:
        raise RuntimeError("must be called from within an exception")
    exc_name = typ.__name__
    print(
        f"{colors.CLR}{colors.BOLD}{colors.RED}--- {exc_name} Trace Begin ---{colors.CLR}"
    )
    traceback.print_exception(typ, val, tb)
    print(
        f"{colors.CLR}{colors.BOLD}{colors.RED}--- {exc_name} Trace End ---{colors.CLR}"
    )


def fmt_err_details(msg: str, details: dict):
    lines = [f"{colors.B_RED}>{colors.B_WHITE} {msg}\n"]
    for label, val in details.items():
        lines.append(f"  * {colors.B_YELLOW}{str(label)}: {colors.B_WHITE}{str(val)}\n")
    lines.append(colors.CLR)

    return "".join(lines)


def pp_err_details(msg: str, details: dict):
    print(fmt_err_details(msg, details), flush=True)


class Error(Exception):
    def __init__(self, msg: str, details: Dict[str, Any] = None):
        self.msg = msg
        self.details = {} if details is None else details
        super().__init__(msg)

    def __str__(self):
        return fmt_err_details(self.msg, self.details)

    def __repr__(self):
        return f"<{type(self).__name__}, msg: {self.msg}, details: {self.details}>"
