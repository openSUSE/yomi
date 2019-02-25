config:
  events: no
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
      partitions:
        - number: 1
          size: 256
          type: efi
        - number: 2
          size: 20000
          type: lvm
    /dev/sdb:
      partitions:
        - number: 1
          size: 20000
          type: lvm
    /dev/sdc:
      partitions:
        - number: 1
          size: 20000
          type: lvm

lvm:
  system:
    vgs:
      - /dev/sda2
      - /dev/sdb1
      - /dev/sdc1
    lvs:
      - name: swap
        size: 2000M
      - name: root
        size: 30000M
      - name: home
        size: 20000M
        
filesystems:
  /dev/sda1:
    filesystem: vfat
    mountpoint: /boot/efi
    # fat: 32
  /dev/system/swap:
    filesystem: swap
  /dev/system/root:
    filesystem: btrfs
    mountpoint: /
    subvolumes:
      prefix: '@'
      subvolume:
        # - path: home
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
  /dev/system/home:
    filesystem: xfs
    mountpoint: /home

bootloader:
  device: /dev/sda

software:
  repositories:
    repo-oss: "http://download.opensuse.org/tumbleweed/repo/oss"
  packages:
    - patterns-base-base
    - kernel-default

users:
  - username: root
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
  - username: aplanas
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
