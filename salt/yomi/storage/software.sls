{% set config = pillar['config'] %}

{% if 'raid' in pillar or 'lvm' in pillar or config.get('snapper', False) %}
include:
  {% if 'raid' in pillar %}
  - .raid.software
  {% endif %}
  {% if 'lvm' in pillar %}
  - .lvm.software
  {% endif %}
  {% if config.get('snapper', False) %}
  - .snapper.software
  {% endif %}
{% endif %}