{% import 'macros.yml' as macros %}

{% set software = pillar['software'] %}
{% set software_config = software.get('config', {}) %}

{{ macros.log('module', 'freeze_chroot') }}
freeze_chroot:
  module.run:
    - freezer.freeze:
      - name: yomi-chroot
      - includes: [pattern]
      - root: /mnt
    - unless: "[ -e /var/cache/salt/minion/freezer/yomi-chroot-pkgs.yml ]"

{{ macros.log('pkg', 'install_python3-base') }}
install_python3-base:
  pkg.installed:
    - name: python3-base
    - resolve_capabilities: yes
  {% if software_config.get('minimal') %}
    - no_recommends: yes
  {% endif %}
  {% if not software_config.get('verify') %}
    - skip_verify: yes
  {% endif %}
    - root: /mnt
    - require:
      - mount: mount_/mnt
