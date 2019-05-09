{% set config = pillar['config'] %}

{% if 'salt-minion' in pillar %}
include:
  {% if 'salt-minion' in pillar %}
  - .salt-minion.software
  {% endif %}
{% endif %}
