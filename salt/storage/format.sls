{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
mkfs_partition_{{ device }}:
  formatted.formatted:
    - name: {{ device }}
    - fs_type: {{ info.filesystem }}
    - require:
      - partitioned: create_partition_{{ device }}
{% endfor %}
