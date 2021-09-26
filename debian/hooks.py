import json

from qvmctl.shell import sh
from qvmctl.conf import Conf, ImgSpecConf
from pathlib import Path
from qvmctl.error import Error
from typing import Callable, Union
import inspect


class HookError(Error):
    def __init__(self, hook: Callable, msg: str):
        mod = inspect.getmodule(hook)
        mod_fpath = inspect.getfile(mod)
        super().__init__(
            f"error in hook: {hook.__name__}: {msg}",
            {
                "hook": hook.__name__,
                "module": mod,
                "module file": mod_fpath,
            },
        )


def chroot(mount_dir: Union[str, Path], *args):
    if isinstance(mount_dir, Path):
        mount_dir = str(mount_dir.absolute())

    cmd = ["sudo", "chroot", mount_dir]
    cmd.extend(args)
    return sh(cmd)


def set_passwd(conf: Conf, img_spec: ImgSpecConf, img: Path, mount_dir: Path):
    print(repr(img_spec.hook_confs("set_passwd")))
    for hdr, opts in img_spec.hook_confs("set_passwd").items():
        user = opts["user"]
        passwd = opts["passwd"]
        sh(
            [
                "sudo",
                "chroot",
                str(mount_dir.absolute()),
                "bash",
                "-c",
                f"""echo '{user}:{passwd}' | chpasswd""",
            ]
        )


def cp_ssh_pubkey(conf: Conf, img_spec: ImgSpecConf, img: Path, mount_dir: Path):
    for hdr, opts in img_spec.hook_confs("cp_ssh_pubkey").items():
        user = opts["user"]
        home = opts["home"]
        key = Path(opts["key"])
        if not key.exists():
            raise HookError(cp_ssh_pubkey, f"could not find public key '{key}'")
        chroot(mount_dir, "mkdir", "-p", f"{home}/.ssh")
        with open(key, "r") as fh:
            chroot(
                mount_dir,
                "bash",
                "-c",
                f"""echo {fh.read().strip()} >> {home}/.ssh/authorized_keys""",
            )
        chroot(mount_dir, "chown", "-R", f"{user}", f"{home}/.ssh")
        chroot(mount_dir, "chmod", "700", f"{user}", f"{home}/.ssh")
        chroot(mount_dir, "chmod", "600", f"{user}", f"{home}/.ssh/authorized_keys")


def deb_nw_dhcp(conf: Conf, img_spec: ImgSpecConf, img: Path, mount_dir: Path):
    print("hook deb_nw_dhcp")
    for hdr, opts in img_spec.hook_confs("deb_nw_dhcp").items():
        for iface in json.loads(opts["ifaces"]):
            conf = "\n".join([f"auto {iface}", f"iface {iface} inet dhcp"])
            chroot(
                mount_dir,
                "bash",
                "-c",
                f"""echo '{conf}' > /etc/network/interfaces.d/{iface}""",
            )


def deb_pkg_install(conf: Conf, img_spec: ImgSpecConf, img: Path, mount_dir: Path):
    updated = False
    for hdr, opts in img_spec.hook_confs("deb_pkg_install").items():
        if not updated:
            chroot(mount_dir, "apt-get", "update")
        chroot(
            mount_dir,
            "bash",
            "-c",
            f"""DEBIAN_FRONTEND=noninteractive apt-get install -y {" ".join(json.loads(opts["packages"]))}""",
        )


def systemd_service_enable(
    conf: Conf, img_spec: ImgSpecConf, img: Path, mount_dir: Path
):
    for hdr, opts in img_spec.hook_confs("systemd_service_enable").items():
        for service in opts["services"]:
            chroot(mount_dir, "systemctl", "enable", service)
