{% set partitions = pillar['partitions'] %}

{% set label = partitions.get('config', {}).get('label', 'msdos') %}
{% for device, info in partitions.devices.items() %}
create_disk_label_{{ device }}:
  partitioned.labeled:
    - name: {{ device }}
    - label: {{ info.label|default(label) }}

  {% set size_ns = namespace(end_size=0) %}
  {% for partition in info.get('partitions', []) %}
    # TODO(aplanas) When moving it to Python, the partition number will be
    # deduced, so the require section in mkfs_partition will fail
    {% set device = device ~ info.get('number', loop.index) %}
create_partition_{{ device }}:
  partitioned.mkparted:
    - name: {{ device }}
    # TODO(aplanas) If msdos we need to create extended and logical
    - part_type: primary
    - fs_type: {{ {'swap': 'linux-swap', 'linux': 'ext2'}[partition.type] }}
    - start: {{ size_ns.end_size }}MB
    - end: {{ size_ns.end_size + partition.size }}MB
    {% set size_ns.end_size = size_ns.end_size + partition.size %}
  {% endfor %}
{% endfor %}
