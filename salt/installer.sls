{% set config = pillar['config'] %}

include:
  - storage
  - software
  - users
  - bootloader
{% if config.get('snapper', False) %}
  # - .storage.snapper_post_install
{% endif %}
  - .storage.umount
{% if config.get('kexec', True) %}
  - kexec
{% endif %}
