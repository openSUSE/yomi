{% set config = pillar['config'] %}

include:
  - system_software
{% if config.get('snapper', False) %}
  - .storage.snapper.software
{% endif %}
