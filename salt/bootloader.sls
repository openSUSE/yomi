{% set config = pillar['config'] %}

include:
  {% if config.get('snapper', False) %}
  - .storage.snapper.grub2
  {% endif %}
  - grub2
