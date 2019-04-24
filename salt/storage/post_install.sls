{% set config = pillar['config'] %}

include:
{% if config.get('snapper', False) %}
  - .snapper.post_install
{% endif %}
  - .btrfs.post_install
{% if not config.get('kexec', True) %}
  - .umount
{% endif %}
