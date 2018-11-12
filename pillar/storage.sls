config:
  conflict:
    - reuse_if_mountpoint_/home
    - fail
  kexec: no

partitions:
  config:
    label: gpt
  devices:
    /dev/sda:
      # label: gpt
      partitions:
        - number: 1
          size: 20000
          type: linux
        - number: 2
          size: 500
          type: swap

filesystems:
  /dev/sda1:
    filesystem: ext3
    mountpoint: /
  /dev/sda2:
    filesystem: swap

bootloader:
  device: /dev/sda

software:
  repositories:
    repo-oss: "http://download.opensuse.org/tumbleweed/repo/oss"
  packages:
    - patterns-base-base
    - grub2
    - kernel-default

users:
  - username: root
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
  - username: aplanas
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
