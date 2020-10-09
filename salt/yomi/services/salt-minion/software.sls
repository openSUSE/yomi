{% import 'macros.yml' as macros %}

{% set software = pillar['software'] %}
{% set software_config = software.get('config', {}) %}

{{ macros.log('pkg', 'install_salt-minion') }}
install_salt-minion:
  pkg.installed:
    - name: salt-minion
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
