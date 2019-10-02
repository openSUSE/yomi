{% set config = pillar['config'] %}

{% if pillar.get('raid') or pillar.get('lvm') or config.get('snapper') %}
include:
  {% if pillar.get('raid') %}
  - .raid.software
  {% endif %}
  {% if pillar.get('lvm') %}
  - .lvm.software
  {% endif %}
  {% if config.get('snapper') %}
  - .snapper.software
  {% endif %}
{% endif %}
