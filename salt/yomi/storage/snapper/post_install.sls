{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.filesystem == 'btrfs' and info.mountpoint == '/' %}
{{ macros.log('snapper_install', 'snapper_step_four_' ~ device) }}
snapper_step_four_{{ device }}:
  snapper_install.step_four:
    - root: /mnt

{{ macros.log('snapper_install', 'snapper_step_five_' ~ device) }}
snapper_step_five_{{ device }}:
  snapper_install.step_five:
    - root: /mnt
    - snapshot_type: single
    - description: 'after installation'
    - important: yes
    - cleanup: number
  {% endif %}
{% endfor %}
