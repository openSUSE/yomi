{% set partitions = pillar['partitions'] %}

{% set partition_config = partitions.get('config', {}) %}
{% set label = partition_config.get('label', 'msdos') %}
{% set is_uefi = salt['file.directory_exists']('/sys/firmware/efi') %}
{% for device, info in partitions.devices.items() %}
create_disk_label_{{ device }}:
  partitioned.labeled:
    - name: {{ device }}
    - label: {{ info.label|default(label) }}

  {% set size_ns = namespace(end_size=partition_config.get('alignment', 1)) %}
  {% if label == 'gpt' and not is_uefi %}
set_pmbr_boot_{{ device }}:
  partitioned.disk_set:
    - name: {{ device }}
    - flag: pmbr_boot
    - enabled: True
  {% endif %}

  {% for partition in info.get('partitions', []) %}
    # TODO(aplanas) When moving it to Python, the partition number will be
    # deduced, so the require section in mkfs_partition will fail
    {% set device = device ~ info.get('number', loop.index) %}
create_partition_{{ device }}:
  partitioned.mkparted:
    - name: {{ device }}
    # TODO(aplanas) If msdos we need to create extended and logical
    - part_type: primary
    - fs_type: {{ {'swap': 'linux-swap', 'linux': 'ext2', 'boot': 'ext2'}[partition.type] }}
    - start: {{ size_ns.end_size }}MB
    - end: {{ size_ns.end_size + partition.size }}MB
    {% if label == 'gpt' and not is_uefi and partition.type == 'boot' %}
    - flags: [bios_grub]
    {% endif %}
    {% set size_ns.end_size = size_ns.end_size + partition.size %}
  {% endfor %}
{% endfor %}
