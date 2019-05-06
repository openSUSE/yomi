{% import 'macros.yml' as macros %}

{% set services = pillar.get('services', {}) %}

include:
  - .network

{% for service in services.get('enabled', []) %}
{{ macros.log('module', 'enable_service_' ~ service) }}
enable_service_{{ service }}:
  module.run:
    - service.enable:
      - name: {{ service }}
      - root: /mnt
    - unless: find /mnt/etc/systemd/system -name '{{ service }}*' | grep -q .
{% endfor %}

{% for service in services.get('disabled', []) %}
{{ macros.log('module', 'disable_service_' ~ service) }}
disable_service_{{ service }}:
  module.run:
    - service.disable:
      - name: {{ service }}
      - root: /mnt
    - onlyif: find /mnt/etc/systemd/system -name '{{ service }}*' | grep -q .
{% endfor %}
