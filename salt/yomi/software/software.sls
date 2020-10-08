{% import 'macros.yml' as macros %}

{% set software = pillar['software'] %}
{% set software_config = software.get('config', {}) %}

{% for alias, repository in software.get('repositories', {}).items() %}
  {% if repository is mapping %}
    {% set url = repository['url'] %}
  {% else %}
    {% set url = repository %}
    {% set repository = {} %}
  {% endif %}
{{ macros.log('pkgrepo', 'add_repository_' ~ alias) }}
add_repository_{{ alias }}:
  pkgrepo.managed:
    - baseurl: {{ url }}
    - name: {{ alias }}
  {% if repository.get('name') %}
    - humanname: {{ repository.name }}
  {% endif %}
    - enabled: {{ repository.get('enabled', software_config.get('enabled', 'yes')) }}
    - refresh: {{ repository.get('refresh', software_config.get('refresh', 'yes')) }}
    - priority: {{ repository.get('priority', 0) }}
    - gpgcheck: {{ repository.get('gpgcheck', software_config.get('gpgcheck', 'yes')) }}
    - gpgautoimport: {{ repository.get('gpgautoimport', software_config.get('gpgautoimport', 'yes')) }}
    - cache: {{ repository.get('cache', software_config.get('cache', 'no')) }}
    - root: /mnt
    - require:
      - mount: mount_/mnt
{% endfor %}

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
    - no_recommends: yes
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
