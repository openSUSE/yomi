{% import 'macros.yml' as macros %}

{% set bootloader = pillar['bootloader'] %}
{% set arch = {'aarch64': 'arm64'}.get(grains['cpuarch'], grains['cpuarch'])%}

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
    - no_recommends: yes
    - root: /mnt
    - require:
      - mount: mount_/mnt
