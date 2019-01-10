{% set config = pillar['config'] %}

include:
  - system_software
  - .bootloader.software
{% if config.get('snapper', False) %}
  - .storage.snapper.software
{% endif %}
