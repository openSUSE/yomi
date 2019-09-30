{% if pillar.get('salt-minion', {}) %}
include:
  {% if pillar.get('salt-minion', {}) %}
  - .salt-minion.software
  {% endif %}
{% endif %}
  