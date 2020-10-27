{% import 'macros.yml' as macros %}

{% set software = pillar['software'] %}
{% set software_config = software.get('config', {}) %}

{{ macros.log('pkg', 'install_snapper') }}
install_snapper:
  pkg.installed:
    - pkgs:
      - snapper
      - grub2-snapper-plugin
      - snapper-zypp-plugin
      - btrfsprogs
  {% if software_config.get('minimal') %}
    - no_recommends: yes
  {% endif %}
  {% if not software_config.get('verify') %}
    - skip_verify: yes
  {% endif %}
    - root: /mnt
    - require:
      - mount: mount_/mnt
