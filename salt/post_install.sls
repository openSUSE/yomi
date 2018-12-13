{% set config = pillar['config'] %}

{% if config.get('snapper', False) or not config.get('kexec', True)%}
include:
  {% if config.get('snapper', False) %}
  - .storage.snapper.post_install
  {% endif %}
  {% if not config.get('kexec', True) %}
  - .storage.umount
  {% endif %}
{% endif %}