{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.filesystem == 'btrfs' and info.mountpoint == '/' %}
snapper_step_one_{{ device }}:
  snapper_install.step_one:
    - device: {{ device }}
    - description: 'first root filesystem'

snapper_step_two_{{ device }}:
  snapper_install.step_two:
    - device: {{ device }}
    - prefix: "{{ info.subvolumes.get('prefix') }}"
  {% endif %}
{% endfor %}
