{% import 'macros.yml' as macros %}

{% set bootloader = pillar['bootloader'] %}
{% set arch = {'aarch64': 'arm64'}.get(grains['cpuarch'], grains['cpuarch'])%}

{% set software = pillar['software'] %}
{% set software_config = software.get('config', {}) %}

{{ macros.log('pkg', 'install_grub2') }}
install_grub2:
  pkg.installed:
    - pkgs:
      - grub2
{% if bootloader.get('theme') %}
      - grub2-branding
{% endif %}
{% if grains['efi'] %}
      - grub2-{{ arch }}-efi
  {% if grains['efi-secure-boot'] %}
      - shim
  {% endif %}
{% endif %}
    - resolve_capabilities: yes
  {% if software_config.get('minimal') %}
    - no_recommends: yes
  {% endif %}
  {# TODO: We should migrate the rpm keys #}
  {% if software_config.get('transfer') %}
    - skip_verify: yes
  {% endif %}
    - root: /mnt
    - require:
      - mount: mount_/mnt
