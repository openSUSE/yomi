{% set config = pillar['config'] %}

include:
  - .btrfs.subvolume
{% if config.get('snapper', False) %}
  - .snapper.subvolume
{% endif %}
