{% import 'macros.yml' as macros %}

{% set bootloader = pillar['bootloader'] %}
{% set is_uefi = grains['efi'] %}
{% set is_secure_boot = grains['efi-secure-boot'] %}

{{ macros.log('cmd', 'grub2_install') }}
grub2_install:
  cmd.run:
{% if is_uefi %}
  {% if is_secure_boot %}
    - name: shim-install --config-file=/boot/grub2/grub.cfg
  {% else %}
    - name: grub2-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=GRUB
  {% endif %}
    - creates: /mnt/boot/efi/EFI/grub2
{% else %}
    - name: grub2-install --force {{ bootloader.device }}
    - unless: dd bs=512 count=1 if={{ bootloader.device }} 2>/dev/null | strings | grep -q 'GRUB'
{% endif %}
{% if 'lvm' in pillar %}
    - binds: [/run]
    - env:
      - LVM_SUPPRESS_FD_WARNINGS: 1
{% endif %}
    - root: /mnt
    - require:
      - cmd: grub2_mkconfig
