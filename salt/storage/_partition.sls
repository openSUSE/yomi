{% import 'macros.yml' as macros %}

{% set partitions = pillar['partitions'] %}
{% set is_uefi = grains['efi'] %}

{% set partition_config = partitions.get('config', {}) %}
{% set label = partition_config.get('label', 'msdos') %}

{% for device, info in partitions.devices.items() if filter(device) %}
{{ macros.log('partitioned', 'create_disk_label_' ~ device) }}
create_disk_label_{{ device }}:
  partitioned.labeled:
    - name: {{ device }}
    - label: {{ info.label|default(label) }}

  {% if label == 'gpt' and not is_uefi %}
{{ macros.log('partitioned', 'set_pmbr_boot_' ~ device) }}
set_pmbr_boot_{{ device }}:
  partitioned.disk_set:
    - name: {{ device }}
    - flag: pmbr_boot
    - enabled: True
  {% endif %}

  {% set size_ns = namespace(end_size=partition_config.get('initial_gap', 1)) %}
  {% for partition in info.get('partitions', []) %}
    {% if partition.type not in ('swap', 'linux', 'boot', 'efi', 'lvm', 'raid') %}
      {% raise('Partition type {} not recognized'.format(partition.type) %}
    {% endif %}
    # TODO(aplanas) When moving it to Python, the partition number will be
    # deduced, so the require section in mkfs_partition will fail
    {% set partition_id = device ~ ('p' if salt.filters.is_raid(device) else '') ~ info.get('number', loop.index) %}
    {% set partition_id = info.get('id', partition_id) %}
{{ macros.log('partitioned', 'create_partition_' ~ partition_id) }}
create_partition_{{ partition_id }}:
  partitioned.mkparted:
    - name: {{ partition_id }}
    # TODO(aplanas) If msdos we need to create extended and logical
    - part_type: primary
    - fs_type: {{ {'swap': 'linux-swap', 'efi': 'fat16'}.get(partition.type, 'ext2') }}
    - start: {{ size_ns.end_size }}MB
    - end: {{ size_ns.end_size + partition.size }}MB
    {% if partition.type == 'raid' %}
    - flags: [raid]
    {% elif partition.type == 'lvm' %}
    - flags: [lvm]
    {% elif label == 'gpt' and not is_uefi and partition.type == 'boot' %}
    - flags: [bios_grub]
    {% elif label == 'gpt' and is_uefi and partition.type == 'efi' %}
    - flags: [esp]
    {% endif %}
    {% set size_ns.end_size = size_ns.end_size + partition.size %}
  {% endfor %}
{% endfor %}
