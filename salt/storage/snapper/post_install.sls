{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.filesystem == 'btrfs' and info.mountpoint == '/' %}
snapper_step_four_{{ device }}:
  snapper_install.step_four:
    - root: /mnt

snapper_step_five_{{ device }}:
  snapper_install.step_five:
    - root: /mnt
    - snapshot_type: single
    - description: 'after installation'
    - important: True
    - cleanup: number
  {% endif %}
{% endfor %}
