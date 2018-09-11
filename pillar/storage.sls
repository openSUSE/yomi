storage:
  disk:
    /dev/sda:
      # type: gpd
      partitions:
        - size: 20000
          type: ext4
          mountpoint: /
        - size: 500
          type: linux-swap

install:
  repo: "http://download.opensuse.org/tumbleweed/repo/oss"
  packages:
    - patterns-base-base
    - grub2
    - kernel-default
  users:
    - username: root
      password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
    - username: aplanas
      password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
