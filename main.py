import typer
import sys
from typing import Dict, Any
from pathlib import Path
from qvmctl.cmds import build
from qvmctl.conf import ImgSpecConf, Conf
from subprocess import CalledProcessError
from qvmctl.shell import sh

app = typer.Typer()


conf_arg = typer.Option(
    Path.home() / ".qvmctl.ini",
    help="path to your vm configuration file",
    dir_okay=False,
    file_okay=True,
    resolve_path=True,
)


img_spec_arg = typer.Argument(
    default=...,
    help="path to the spec describing the image to create",
    dir_okay=False,
    file_okay=True,
    resolve_path=True,
    exists=True,
    metavar="img-spec",
)

img_file_arg = typer.Argument(
    default=...,
    help="path to the image file",
    dir_okay=False,
    file_okay=True,
    resolve_path=True,
    metavar="IMG",
)


def get_env() -> Dict[str, Any]:
    return {"home": str(Path.home().absolute())}


@app.command()
def build_img(
    config: Path = conf_arg,
    force: bool = typer.Option(default=False),
    spec: Path = img_spec_arg,
    img: Path = img_file_arg,
):

    # look for hooks in dir local to img spec
    sys.path.insert(1, str(spec.parent.absolute()))

    env = get_env()
    conf = Conf(env=env, confs=[config])
    img_conf = ImgSpecConf(env=env, confs=[spec])
    try:
        build.build(conf, img_conf, img, force)
    except CalledProcessError:
        sys.exit(1)


@app.command()
def run(config: Path = conf_arg, vm_name: str = typer.Argument(...)):

    env = get_env()
    conf = Conf(env=env, confs=[config])
    vm_conf = conf.vm(vm_name)
    qemu_cmd = vm_conf.qemu_cmd()
    try:
        sh(qemu_cmd)
    except CalledProcessError:
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.append("--help")
    app()
