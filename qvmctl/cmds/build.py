import configparser
from qvmctl.conf import EnvInterpolator, Conf, ImgSpecConf
from pathlib import Path
from typing import Dict, Any, Union
from tempfile import TemporaryDirectory
import typer
from qvmctl.shell import sh
from contextlib import contextmanager
from qvmctl.hooks import resolv_hook


@contextmanager
def mount_loop(img: Union[str, Path], mount_dir: Union[str, Path]):
    if isinstance(img, Path):
        img = str(img.absolute())

    if isinstance(mount_dir, Path):
        mount_dir = str(mount_dir.absolute())

    sh(["sudo", "mount", "-o", "loop", img, mount_dir])
    try:
        yield
    finally:
        sh(["sudo", "umount", mount_dir])


def read_img_spec(spec: Path) -> Dict[str, Any]:
    cp = configparser.ConfigParser(
        interpolation=EnvInterpolator({"home": str(Path.home().resolve())})
    )
    cp.read(str(spec))
    return {section: dict(cp.items(section)) for section in cp.sections()}


def build(conf: Conf, spec: ImgSpecConf, img: Path, force: bool):
    if img.exists():
        if force:
            img.unlink()
        else:
            raise typer.BadParameter("img exists")

    img_conf = spec.img
    img_opts = spec.opts
    with TemporaryDirectory() as mount_dir:
        sh(
            [
                conf.global_vars.qemu_bin("qemu-img"),
                "create",
                str(img.absolute()),
                img_conf.size,
            ]
        )
        sh(["mkfs.ext2", str(img.absolute())])
        with mount_loop(img, mount_dir):
            sh(
                [
                    "sudo",
                    "debootstrap",
                    "--arch",
                    "amd64",
                    img_opts.get("release", "buster"),
                    mount_dir,
                ]
            )
            for hook in img_conf.hooks:
                fn = resolv_hook(hook)
                fn(conf, spec, img, Path(mount_dir))
