{% import 'macros.yml' as macros %}

{% set config = pillar['config'] %}

{{ macros.log('pkg', 'install_grub2') }}
install_grub2:
  pkg.installed:
    - pkgs:
      - grub2
{% if config.get('grub2_theme') %}
      - grub2-branding-openSUSE
{% endif %}
{% if grains['efi'] %}
      - grub2-x86_64-efi
  {% if grains['efi-secure-boot'] %}
      - shim
  {% endif %}
{% endif %}
    - no_recommends: yes
    - root: /mnt
    - require:
      - mount: mount_/mnt
