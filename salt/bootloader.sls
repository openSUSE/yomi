{% set bootloader = pillar['bootloader'] %}

mkinitrd:
  cmd.run:
    - name: mkinitrd -d /mnt -b /mnt/boot
    - creates: /mnt/boot/initrd

grub2_mkconfig_chroot:
  cmd.run:
    - name: grub2-mkconfig -o /boot/grub2/grub.cfg
    - root: /mnt
    - creates: /mnt/boot/grub2/grub.cfg

grub2_install:
  cmd.run:
    - name: grub2-install --boot-directory=/mnt/boot {{ bootloader.device }} --force
    - require:
      - cmd: grub2_mkconfig_chroot
    - unless: dd bs=512 count=1 if={{ bootloader.device }} 2>/dev/null | strings | grep -q 'GRUB'
