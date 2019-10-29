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

{% if config.get('grub2_theme') %}
{{ macros.log('file', 'config_grub2_theme') }}
config_grub2_theme:
  file.append:
    - name: /mnt/etc/default/grub
    - text:
      - GRUB_TERMINAL={{ "gfxterm" if not config.get('grub2_console') else "console" }}
      - GRUB_GFXMODE="{{ bootloader.get('gfxmode', 'auto') }}"
      - GRUB_BACKGROUND=
      # - GRUB_THEME="/boot/grub2/themes/openSUSE/theme.txt"
{% endif %}

{% set kernel = bootloader.get('kernel', 'splash=silent quiet') %}
{% if config.get('grub2_console') %}
  {% set kernel = kernel ~ ' console=tty0 console=ttyS0,115200' %}
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
      - GRUB_CMDLINE_LINUX_DEFAULT="{{ kernel }}"
      - GRUB_DISABLE_OS_PROBER="{{ true if bootloader.get('disable_os_prober') else false }}"

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
