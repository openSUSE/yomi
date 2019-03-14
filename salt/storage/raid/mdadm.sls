{% import 'macros.yml' as macros %}

{% set raid = pillar.get('raid', {}) %}

{% for device, info in raid.items() %}
{{ macros.log('raid', 'create_raid_' ~ device) }}
create_raid_{{ device }}:
  raid.present:
    - name: {{ device }}
    - level: {{ info.level }}
    - devices: {{ info.devices }}
  {% for key, value in info.items() if key not in ('level', 'devices') %}
    - {{ key }}: {{ value }}
  {% endfor %}
{% endfor %}
