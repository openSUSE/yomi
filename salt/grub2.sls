{% set bootloader = pillar['bootloader'] %}
{% set is_uefi = grains['efi'] %}

mkinitrd:
  cmd.run:
    - name: mkinitrd -d /mnt -b /mnt/boot
    - creates: /mnt/boot/initrd

{% if is_uefi %}
grub2_config_EFI:
  file.append:
    - name: /mnt/etc/default/grub
    - text: GRUB_USE_LINUXEFI="true"
{% endif %}

grub2_mkconfig:
  cmd.run:
    - name: grub2-mkconfig -o /boot/grub2/grub.cfg
    - root: /mnt
    - creates: /mnt/boot/grub2/grub.cfg

grub2_install:
  cmd.run:
{% if is_uefi %}
    # - name: grub2-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=GRUB
    - name: shim-install --config-file=/boot/grub2/grub.cfg
{% else %}
    - name: grub2-install --force {{ bootloader.device }}
{% endif %}
    - root: /mnt
    - require:
      - cmd: grub2_mkconfig
    # TODO do not work for UEFI
    - unless: dd bs=512 count=1 if={{ bootloader.device }} 2>/dev/null | strings | grep -q 'GRUB'
