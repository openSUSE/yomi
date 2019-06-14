{% import 'macros.yml' as macros %}

{% set lvm = pillar.get('lvm', {}) %}

{% for group, group_info in lvm.items() %}
  {% set devices = [] %}
  {% for device in group_info['devices'] %}
    {% set info = {} %}
    {# We can store the device information inside a dict #}
    {% if device is mapping %}
      {% set info = device %}
      {% set device = device['name'] %}
    {% endif %}
  {% do devices.append(device) %}
{{ macros.log('lvm', 'create_physical_volume_' ~ device) }}
create_physical_volume_{{ device }}:
  lvm.pv_present:
    - name: {{ device }}
    {% for key, value in info.items() if key != 'name' %}
    - {{ key }}: {{ value }}
    {% endfor %}
  {% endfor %}

{{ macros.log('lvm', 'create_virtual_group_' ~ group) }}
create_virtual_group_{{ group }}:
  lvm.vg_present:
    - name: {{ group }}
    - devices: [{{ ', '.join(devices) }}]
    {% for key, value in group_info.items() if key not in ('devices', 'volumes') %}
    - {{ key }}: {{ value }}
    {% endfor %}

  {% for volume in group_info['volumes'] %}
{{ macros.log('lvm', 'create_logical_volume_' ~ volume['name']) }}
create_logical_volume_{{ volume['name'] }}:
  lvm.lv_present:
    - name: {{ volume['name'] }}
    - vgname: {{ group }}
    {% for key, value in volume.items() if key not in ('name', 'vgname') %}
    - {{ key }}: {{ value }}
    {% endfor %}
  {% endfor %}
{% endfor %}
