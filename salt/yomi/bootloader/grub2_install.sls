{% import 'macros.yml' as macros %}

{% set bootloader = pillar['bootloader'] %}
{% set arch = {'aarch64': 'arm64'}.get(grains['cpuarch'], grains['cpuarch'])%}

{{ macros.log('cmd', 'grub2_install') }}
grub2_install:
  cmd.run:
{% if grains['efi'] %}
  {% if grains['efi-secure-boot'] %}
    - name: shim-install --config-file=/boot/grub2/grub.cfg
  {% else %}
    - name: grub2-install --target={{ arch }}-efi --efi-directory=/boot/efi --bootloader-id=GRUB
  {% endif %}
    - creates: /mnt/boot/efi/EFI/GRUB
{% else %}
    - name: grub2-install --force {{ bootloader.device }}
    - creates: /mnt/boot/grub2/i386-pc/normal.mod
{% endif %}
{% if pillar.get('lvm') %}
    - binds: [/run]
    - env:
      - LVM_SUPPRESS_FD_WARNINGS: 1
{% endif %}
    - root: /mnt
    - require:
      - cmd: grub2_mkconfig
