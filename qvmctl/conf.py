from configparser import ExtendedInterpolation, ConfigParser
from typing import Dict, Any, List, Union, Optional
import os
from dataclasses import dataclass
import json
from pathlib import Path
from qvmctl.error import Error
from qvmctl.utils import flatten_list


def read_config(env: Dict[str, Any], *confs: str) -> ConfigParser:
    cp = ConfigParser(interpolation=EnvInterpolator(env))
    cp.read(confs)
    return cp


def read_config_dict(env: Dict[str, Any], *confs: str) -> Dict[str, Any]:
    cp = read_config(env, *confs)
    return {section: dict(cp.items(section)) for section in cp.sections()}


class EnvInterpolator(ExtendedInterpolation):
    """Expand %(foo)-style vars from given environment and ENV-style vars ($FOO) from env"""

    def __init__(self, env: Dict[str, Any]) -> None:
        super().__init__()
        self.env = env

    def before_read(self, parser, section, option, value):
        value = super().before_read(parser, section, option, value)
        return os.path.expanduser(os.path.expandvars(value).format(**self.env))


@dataclass
class ImgSpec:
    size: str
    hooks: List[str]

    def __post_init__(self):
        if isinstance(self.hooks, str):
            self.hooks = json.loads(self.hooks)


@dataclass
class ConfGlobal:
    qemu_bindir: Union[Path, str]

    def __post_init__(self):
        if isinstance(self.qemu_bindir, str):
            self.qemu_bindir = Path(self.qemu_bindir)
        if not self.qemu_bindir.exists():
            raise ValueError(f"qemu_bindir: {self.qemu_bindir} does not exist")
        elif not self.qemu_bindir.is_dir():
            raise ValueError(f"qemu_bindir: {self.qemu_bindir} is not a directory")

    def qemu_bin(self, name: str) -> str:
        return str((self.qemu_bindir / name).absolute())


class BaseConf:
    def __init__(
        self, *, confs: List[Union[Path, str]], env: Optional[Dict[str, Any]] = None
    ):
        self.confs = [str(c.absolute()) if isinstance(c, Path) else c for c in confs]
        self.env = {} if env is None else env
        self.conf = read_config(self.env, *self.confs)

    @property
    def to_dict(self):
        return {
            section: dict(self.conf.items(section)) for section in self.conf.sections()
        }

    def __repr__(self) -> str:
        return f"""<{type(self).__name__}, confs: {", ".join(self.confs)}, env: {repr(self.env)}>"""

    def __str__(self) -> str:
        return self.__repr__()


class Conf(BaseConf):
    @property
    def global_vars(self) -> ConfGlobal:
        return ConfGlobal(**dict(self.conf.items("global")))

    def qemu_bin(self, name: str) -> str:
        return self.global_vars.qemu_bin(name)

    def vm(self, name: str):
        return VirtualMachineConf(self, name)


class ImgSpecConf(BaseConf):
    """Read contents of a image spec ini file."""

    @property
    def img(self) -> ImgSpec:
        return ImgSpec(**dict(self.conf.items("img")))

    @property
    def opts(self) -> Dict[str, Any]:
        return dict(self.conf.items("img.options"))

    def hook_confs(self, hook_name: str):
        return {
            section: dict(self.conf.items(section))
            for section in self.conf.sections()
            if section.startswith(f"hook.{hook_name}")
        }


_unset = object()


class VirtualMachineConf:
    __unset = object()

    def __init__(self, conf: Conf, name: str):
        self.__conf = conf
        self.__name = name
        self.__attrs = []
        self.__vals = dict(conf.conf.items(self.vm_name))
        for attr, val in self.__vals.items():
            setattr(self, attr, val)
            self.__attrs.append(attr)

    @property
    def vm_name(self):
        return f"vm.{self.__name}"

    def __quemu_vm_bin(self) -> str:
        # TODO: don't hard-code
        return self.__conf.qemu_bin("qemu-system-x86_64")

    def _getattr(self, attr_name: str, default=_unset):
        val = getattr(self, attr_name, default)
        if val == _unset:
            raise Error(
                "attribute not set in config",
                {"vm section": self.vm_name, "attr": attr_name},
            )
        return val

    def _mounts(self):
        return {
            k: v
            for k, v in self.__conf.conf.items()
            if k.startswith(f"{self.vm_name}.mount.")
        }

    def _qemu_cmd_base(self) -> List[str]:
        return [
            self.__quemu_vm_bin(),
            "-serial",
            "stdio",
            "-display",
            "none",
            "-kernel",
            self._getattr("kernel_path"),
            "--append",
            self._getattr("kernel_cmd"),
            "-enable-kvm",
            "-cpu",
            "host",
            "-smp",
            self._getattr("cpus"),
            "-netdev",
            "user,id=network0,hostfwd=tcp::2022-:22",
            "-drive",
            f"""file={self._getattr("img")},index=0,media=disk,format=raw""",
            "--device",
            "e1000,netdev=network0",
            "-m",
            self._getattr("memory"),
        ]

    def qemu_cmd(self) -> List[str]:
        extra_settings = []
        for mount_hdr, opts in self._mounts().items():
            id = mount_hdr.split(".")[-1]
            path = opts["vm_path"]
            tag = opts["tag"]
            extra_settings.extend(
                [
                    "-fsdev",
                    f"local,security_model=passthrough,id=fsdev{id},path={path}",
                    "-device",
                    f"virtio-9p-pci,id=fs{id},fsdev=fsdev{id},mount_tag={tag}",
                ]
            )
        return flatten_list(
            [
                *self._qemu_cmd_base(),
                *extra_settings,
            ]
        )

    def __repr__(self):
        attrs = ", ".join({f"{k}: {v}" for k, v in self.__vals.items()})
        return f"""<{type(self).__name__}, {attrs}>"""
