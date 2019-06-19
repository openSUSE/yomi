{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.filesystem == 'btrfs' and 'ro' in info.get('options', []) %}
{{ macros.log('btrfs', 'set_property_ro_' ~ info.mountpoint) }}
set_property_ro_{{ info.mountpoint }}:
  btrfs.properties:
    - name: {{ info.mountpoint }}
    - device: {{ device }}
    - use_default: yes
    - ro: yes
  {% endif %}
{% endfor %}
