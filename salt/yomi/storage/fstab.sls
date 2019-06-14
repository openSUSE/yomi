{% set config = pillar['config'] %}

include:
  - .create_fstab
  - .device.fstab
  - .btrfs.fstab
{% if config.get('snapper', False) %}
  - .snapper.fstab
{% endif %}
