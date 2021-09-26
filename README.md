# QVMCTL

**This is an experiment and the code is super hacky, make of it what you will**.

A tool to build and run QEMU VM's. VM images are built from spec files
which can be extended by hooks. For example, the following builds a
base Debian image with [debootstrap](https://wiki.debian.org/Debootstrap).
The spec then defines a series of post-customization options to perform
by referencing hooks and providing their required parameters:

```ini
[img]
size=1g
hooks=[
    "hooks:set_passwd",
    "hooks:cp_ssh_pubkey",
    "hooks:deb_nw_dhcp",
    "hooks:deb_pkg_install"
    ]

[img.options]
release=buster

[hook.set_passwd/admin]
user=root
passwd=toor

[hook.cp_ssh_pubkey/personal]
key=~/.ssh/id_rsa.pub
user=root
home=/root

[hook.deb_nw_dhcp]
ifaces=["eth0"]

[hook.deb_pkg_install]
packages=[
    "ssh"
    ]

[hook.systemd_service_enable]
services=["ssh"]
```

Through hooks, we:

* set the root password
* configure the VM's eth0 NIC for DHCP
* installing and enabling the OpenSSH server
* copy our SSH public key to the VM root account

To run VM's via qvmctl, write a configuration file which defines the
kernel to use and the host mounts to support:

```ini
[global]
qemu_bindir = {home}/repos/qemu/build

[vm.my_vm]
kernel_path = {home}/repos/linux/arch/x86/boot/bzImage
kernel_cmd = root=/dev/sda rw console=tty0 console=ttyS0,115200 net.ifnames=0 biosdevname=0
img = {home}/repos/qvmctl/debian.img
cpus = 8
memory = 16g

[vm.my_vm.mount.0]
vm_path = /lib/modules
tag = modshare

[vm.my_vm.mount.1]
vm_path = {home}
tag = homeshare

[vm.my_vm.mount.2]
vm_path = /usr/local/lib
tag = local_libshare
```

## Issues / Needs work
* can only build Debian images currently - needs an extensible base OS build routine.
* most QEMU flags/arguments are fixed, need further support for custom flags
* Linux-centric -- assumes an external Linux kernel to boot.
* Port-forwarding is not configurable, at the moment, SSH is available via 2022

