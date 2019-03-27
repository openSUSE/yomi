{% import 'macros.yml' as macros %}

{% set partitions = salt.partmod.prepare_partition_data(pillar['partitions']) %}
{% set is_uefi = grains['efi'] %}

{% for device, device_info in partitions.items() if filter(device) %}
{{ macros.log('partitioned', 'create_disk_label_' ~ device) }}
create_disk_label_{{ device }}:
  partitioned.labeled:
    - name: {{ device }}
    - label: {{ device_info.label }}

  {% if device_info.pmbr_boot %}
{{ macros.log('partitioned', 'set_pmbr_boot_' ~ device) }}
set_pmbr_boot_{{ device }}:
  partitioned.disk_set:
    - name: {{ device }}
    - flag: pmbr_boot
    - enabled: True
  {% endif %}

  {% for partition in device_info.get('partitions', []) %}
{{ macros.log('partitioned', 'create_partition_' ~ partition.part_id) }}
create_partition_{{ partition.part_id }}:
  partitioned.mkparted:
    - name: {{ partition.part_id }}
    - part_type: {{ partition.part_type }}
    - fs_type: {{ partition.fs_type }}
    - start: {{ partition.start }}
    - end: {{ partition.end }}
    {% if partition.flags %}
    - flags: {{ partition.flags }}
    {% endif %}
  {% endfor %}
{% endfor %}
