{% set config = pillar['config'] %}

include:
  - storage
  - software
  - users
  - bootloader
  - services
  - post_install
{% if config.get('kexec', True) %}
  - kexec
{% endif %}
