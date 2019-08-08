{% set config = pillar['config'] %}

include:
{% if config.get('snapper', False) %}
  - .snapper.post_install
{% endif %}
  - .mark
  - .btrfs.post_install
{% if not config.get('reboot', True) %}
  - .umount
{% endif %}
