config:
  conflict:
    - reuse_if_mountpoint_/home
    - fail
  kexec: yes
  snapper: yes
  grub2_theme: yes

partitions:
  config:
    label: gpt
    # Units in MB
    alignment: 1
  devices:
    /dev/sda:
      # label: gpt
      partitions:
        # - number: 1
        #   size: 4
        #   type: boot
        - number: 1
          size: 512
          type: efi
        - number: 2
          size: 20000
          type: linux
        - number: 3
          size: 500
          type: swap

filesystems:
  /dev/sda1:
    filesystem: vfat
    mountpoint: /boot/efi
    # fat: 32
  /dev/sda2:
    filesystem: btrfs
    mountpoint: /
    subvolumes:
      prefix: '@'
      subvolume:
        - path: home
        - path: opt
        - path: root
        - path: srv
        - path: tmp
        - path: usr/local
        - path: var
          copy_on_write: no
        - path: boot/grub2/i386-pc
          archs: ['i386', 'x86_64']
        - path: boot/grub2/x86_64-efi
          archs: ['x86_64']
  /dev/sda3:
    filesystem: swap

bootloader:
  device: /dev/sda

software:
  repositories:
    repo-oss: "http://download.opensuse.org/tumbleweed/repo/oss"
  packages:
    - patterns-base-base
    - grub2
    - grub2-x86_64-efi
    - shim
    - kernel-default

users:
  - username: root
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
  - username: aplanas
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
