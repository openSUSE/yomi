{% set config = pillar['config'] %}
{% set is_uefi = grains['efi'] %}

{% if config.get('snapper', False) %}
include:
  {% if config.get('snapper', False) %}
  - storage.snapper.grub2-mkconfig
  {% endif %}
{% endif %}

{% if config.get('grub2_theme', False) %}
{% endif %}

{% if is_uefi %}
config_grub2_efi:
  file.append:
    - name: /mnt/etc/default/grub
    - text: GRUB_USE_LINUXEFI="true"
{% endif %}

grub2_mkconfig:
  cmd.run:
    - name: grub2-mkconfig -o /boot/grub2/grub.cfg
    - root: /mnt
    - creates: /mnt/boot/grub2/grub.cfg
