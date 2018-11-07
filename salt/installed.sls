{% set config = pillar['config'] %}

include:
  - storage
  - software
  - users
  - bootloader
{% if config.get('kexec', True) %}
  - kexec
{% endif %}
