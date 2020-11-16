{% import 'macros.yml' as macros %}

{% set software = pillar['software'] %}
{% set software_config = software.get('config', {}) %}

{% if software_config.get('minimal') %}
{{ macros.log('file', 'config_zypp_minimal_host') }}
config_zypp_minimal_host:
  file.append:
    - name: /etc/zypp/zypp.conf
    - text:
        - solver.onlyRequires = true
        - rpm.install.excludedocs = yes
        - multiversion =
{% endif %}

{% if software.get('packages') %}
{{ macros.log('pkg', 'install_packages') }}
install_packages:
  pkg.installed:
    - pkgs: {{ software.packages }}
  {% if software_config.get('minimal') %}
    - no_recommends: yes
  {% endif %}
  {% if not software_config.get('verify') %}
    - skip_verify: yes
  {% endif %}
    - includes: [product, pattern]
    - root: /mnt
{% endif %}

{% if software_config.get('minimal') %}
{{ macros.log('file', 'config_zypp_minimal') }}
config_zypp_minimal:
  file.append:
    - name: /mnt/etc/zypp/zypp.conf
    - text:
        - solver.onlyRequires = true
        - rpm.install.excludedocs = yes
        - multiversion =
{% endif %}
