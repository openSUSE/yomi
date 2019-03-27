config:
  events: no
  kexec: yes
  snapper: yes
  grub2_theme: yes
  grub2_console: yes

partitions:
  config:
    label: gpt
    initial_gap: 1MB
  devices:
    /dev/sda:
      partitions:
        - number: 1
          size: 20000MB
          type: raid
    /dev/sdb:
      partitions:
        - number: 1
          size: 20000MB
          type: raid
    /dev/sdc:
      partitions:
        - number: 1
          size: 20000MB
          type: raid
    /dev/md0:
      partitions:
        - number: 1
          size: 500MB
          type: efi
        - number: 2
          size: 2000MB
          type: swap
        - number: 3
          size: rest #15000MB
          type: linux

raid:
  /dev/md0:
    level: 1
    devices:
      - /dev/sda1
      - /dev/sdb1
      - /dev/sdc1
    spare-devices: 1
    metadata: 1.0

filesystems:
  /dev/md0p1:
    filesystem: vfat
    mountpoint: /boot/efi
    # fat: 32
  /dev/md0p2:
    filesystem: swap
  /dev/md0p3:
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

bootloader:
  device: /dev/md0

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
