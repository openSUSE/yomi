{% set config = pillar['config'] %}

include:
{% if config.get('snapper') %}
  - .snapper.post_install
{% endif %}
  - .btrfs.post_install
{% if not config.get('reboot', True) %}
  - .umount
{% endif %}
