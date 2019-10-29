{% import 'macros.yml' as macros %}

{% set config = pillar['config'] %}
{% set bootloader = pillar['bootloader'] %}

{% if config.get('snapper') %}
include:
  {% if config.get('snapper') %}
  - ..storage.snapper.grub2_mkconfig
  {% endif %}
{% endif %}

{% if grains['efi'] %}
{{ macros.log('file', 'config_grub2_efi') }}
config_grub2_efi:
  file.append:
    - name: /mnt/etc/default/grub
    - text: GRUB_USE_LINUXEFI="true"
{% endif %}

{% if bootloader.get('theme') %}
{{ macros.log('file', 'config_grub2_theme') }}
config_grub2_theme:
  file.append:
    - name: /mnt/etc/default/grub
    - text:
      - GRUB_TERMINAL="{{ bootloader.get('terminal', 'gfxterm') }}"
      - GRUB_GFXMODE="{{ bootloader.get('gfxmode', 'auto') }}"
      - GRUB_BACKGROUND=
      # - GRUB_THEME="/boot/grub2/themes/openSUSE/theme.txt"
{% endif %}

{{ macros.log('file', 'config_grub2_resume') }}
config_grub2_resume:
  file.append:
    - name: /mnt/etc/default/grub
    - text:
      - GRUB_TIMEOUT=8
{% if not pillar.get('lvm') %}
      - GRUB_DEFAULT="saved"
      # - GRUB_SAVEDEFAULT="true"
{% endif %}

{% set serial_command = bootloader.get('serial_command')%}
{{ macros.log('file', 'config_grub2_config') }}
config_grub2_config:
  file.append:
    - name: /mnt/etc/default/grub
    - text:
      - GRUB_CMDLINE_LINUX_DEFAULT="{{ bootloader.get('kernel', 'splash=silent quiet') }}"
      - GRUB_DISABLE_OS_PROBER="{{ true if bootloader.get('disable_os_prober') else false }}"
{% if serial_command %}
      - GRUB_TERMINAL="serial"
      - GRUB_SERIAL_COMMAND="{{ serial_command }}"
{% endif %}

{{ macros.log('cmd', 'grub2_set_default') }}
grub2_set_default:
  cmd.run:
    - name: (source /etc/os-release; grub2-set-default "${PRETTY_NAME}")
    - root: /mnt
    - onlyif: "[ -e /mnt/etc/os-release ]"
    - watch:
      - file: /mnt/etc/default/grub

{{ macros.log('cmd', 'grub2_mkconfig') }}
grub2_mkconfig:
  cmd.run:
    - name: grub2-mkconfig -o /boot/grub2/grub.cfg
    - root: /mnt
{% if pillar.get('lvm') %}
    - binds: [/run]
{% endif %}
    - watch:
      - file: /mnt/etc/default/grub
