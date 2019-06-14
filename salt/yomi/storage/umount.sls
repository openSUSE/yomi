{% set config = pillar['config'] %}

include:
{% if config.get('snapper', False) %}
  - .snapper.umount
{% endif %}
  - .btrfs.umount
  - .device.umount
