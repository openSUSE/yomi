{% import 'macros.yml' as macros %}

{% set partitions = salt.partmod.prepare_partition_data(pillar['partitions']) %}

{% for device in partitions %}
{{ macros.log('module', 'wipe_' ~ device) }}
wipe_{{ device }}:
  module.run:
    - devices.wipe:
      - device: {{ device }}
{% endfor %}