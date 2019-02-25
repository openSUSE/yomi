{% import 'macros.yml' as macros %}

{% set lvm = pillar.get('lvm', {}) %}

{% for group, group_info in lvm.items() %}
  {% for device in group_info['vgs'] %}
{{ macros.log('lvm', 'create_physical_volume_' ~ device) }}
create_physical_volume_{{ device }}:
  lvm.pv_present:
    - name: {{ device }}
  {% endfor %}

{{ macros.log('lvm', 'create_virtual_group_' ~ group) }}
create_virtual_group_{{ group }}:
  lvm.vg_present:
    - name: {{ group }}
    - devices: [{{ ', '.join(group_info['vgs']) }}]

  {% for volume in group_info['lvs'] %}
{{ macros.log('lvm', 'create_logical_volume_' ~ volume) }}
create_logical_volume_{{ volume['name'] }}:
  lvm.lv_present:
    - name: {{ volume['name'] }}
    - vgname: {{ group }}
    - size: {{ volume['size'] }}
  {% endfor %}
{% endfor %}
