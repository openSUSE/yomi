{% set config = pillar['config'] %}

include:
  - .btrfs.subvolume
{% if config.get('snapper') %}
  - .snapper.subvolume
{% endif %}
