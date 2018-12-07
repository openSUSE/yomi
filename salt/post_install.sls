{% set config = pillar['config'] %}

include:
{% if config.get('snapper', False) %}
  - .storage.snapper.post_install
{% endif %}
  - .storage.umount
