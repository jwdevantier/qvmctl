from qvmctl.utils import colors


def info(msg: str):
    print(f"{colors.B_BLUE}INFO> {colors.B_WHITE}{msg}{colors.CLR}")


def warn(msg: str):
    print(f"{colors.B_YELLOW}WARN> {colors.B_WHITE}{msg}{colors.CLR}")


def error(msg: str):
    print(f"{colors.B_RED}ERR> {colors.B_WHITE}{msg}{colors.CLR}")
