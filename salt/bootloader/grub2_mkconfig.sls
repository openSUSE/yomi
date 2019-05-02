{% import 'macros.yml' as macros %}

{% set config = pillar['config'] %}
{% set bootloader = pillar['bootloader'] %}
{% set is_uefi = grains['efi'] %}

{% if config.get('snapper', False) %}
include:
  {% if config.get('snapper', False) %}
  - storage.snapper.grub2_mkconfig
  {% endif %}
{% endif %}

{% if is_uefi %}
{{ macros.log('file', 'config_grub2_efi') }}
config_grub2_efi:
  file.append:
    - name: /mnt/etc/default/grub
    - text: GRUB_USE_LINUXEFI="true"
{% endif %}

{% if config.get('grub2_theme', False) %}
{{ macros.log('file', 'config_grub2_theme') }}
config_grub2_theme:
  file.append:
    - name: /mnt/etc/default/grub
    - text:
      - GRUB_TERMINAL="gfxterm"
      - GRUB_GFXMODE="auto"
      - GRUB_BACKGROUND=
      # - GRUB_THEME="/boot/grub2/themes/openSUSE/theme.txt"
{% endif %}

{% set kernel = 'splash=silent quiet' %}
{% if config.get('grub2_console', False) %}
  {% set kernel = kernel ~ ' console=tty0 console=ttyS0,115200' %}
{% endif %}
{% if bootloader.get('kernel', False) %}
  {% set kernel = kernel ~ ' ' ~ bootloader['kernel'] %}
{% endif %}
{{ macros.log('file', 'config_grub2_resume') }}
config_grub2_resume:
  file.append:
    - name: /mnt/etc/default/grub
    - text:
      - GRUB_TIMEOUT=8
{% if 'lvm' not in pillar %}
      - GRUB_DEFAULT="saved"
      # - GRUB_SAVEDEFAULT="true"
{% endif %}
      - GRUB_CMDLINE_LINUX_DEFAULT="{{ kernel }}"
      - GRUB_DISABLE_OS_PROBER="{{ true if bootloader.get('disable_os_prober', False) else false }}"

{{ macros.log('cmd', 'grub2_mkconfig') }}
grub2_mkconfig:
  cmd.run:
    - name: grub2-mkconfig -o /boot/grub2/grub.cfg
    - root: /mnt
{% if 'lvm' in pillar %}
    - binds: [/run]
{% endif %}
    - creates: /mnt/boot/grub2/grub.cfg
