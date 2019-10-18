{% import 'macros.yml' as macros %}

{% set suseconnect = pillar['suseconnect'] %}
{% set suseconnect_config = suseconnect['config'] %}

{{ macros.log('suseconnect', 'register_product') }}
register_product:
  suseconnect.registered:
    - regcode: {{ suseconnect_config['regcode'] }}
{% if suseconnect_config.get('email') %}
    - email: {{ suseconnect_config['email'] }}
{% endif %}
{% if suseconnect_config.get('url') %}
    - url: {{ suseconnect_config['url'] }}
{% endif %}
    - root: /mnt
    - require:
      - mount: mount_/mnt

{% for product in suseconnect.get('products', []) %}
  {% if 'version' in suseconnect_config and 'arch' in suseconnect_config %}
    {% if suseconnect_config['version'] not in product %}
      {% set product = '%s/%s/%s'|format(product, suseconnect_config['version'], suseconnect_config['arch']) %}
    {% endif %}
  {% endif %}
{{ macros.log('suseconnect', 'register_' ~ product) }}
register_{{ product }}:
  suseconnect.registered:
    - regcode: {{ suseconnect_config['regcode'] }}
    - product: {{ product }}
{% if suseconnect_config.get('email') %}
    - email: {{ suseconnect_config['email'] }}
{% endif %}
{% if suseconnect_config.get('url') %}
    - url: {{ suseconnect_config['url'] }}
{% endif %}
    - root: /mnt
    - require:
      - mount: mount_/mnt
{% endfor %}

{% if suseconnect.get('packages') %}
{{ macros.log('pkg', 'install_packages_product') }}
install_packages_product:
  pkg.installed:
    - pkgs: {{ suseconnect.packages }}
    - no_recommends: yes
    - includes: [product, pattern]
    - root: /mnt
    - require:
        - suseconnect: register_product
{% endif %}
