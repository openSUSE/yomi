{% import 'macros.yml' as macros %}

{% set software = pillar['software'] %}
{% set software_config = software.get('config', {}) %}

{% if software_config.get('minimal', False) %}
{{ macros.log('file', 'config_zypp_minimal_host') }}
config_zypp_minimal_host:
  file.append:
    - name: /etc/zypp/zypp.conf
    - text:
        - solver.onlyRequires = true
        - rpm.install.excludedocs = yes
        - multiversion =
{% endif %}

{% for name, repo in software.repositories.items() %}
{{ macros.log('pkgrepo', 'add_repository_' ~ repo) }}
add_repository_{{ repo }}:
  pkgrepo.managed:
    - name: {{ name }}
    - baseurl: {{ repo }}
    - refresh: yes
    - gpgautoimport: yes
    - root: /mnt
    - require:
      - mount: mount_/mnt
{% endfor %}

{{ macros.log('pkg', 'install_packages') }}
install_packages:
  pkg.installed:
    - pkgs: {{ software.packages }}
    - no_recommends: yes
    - includes: [pattern]
    - root: /mnt

{% if software_config.get('minimal', False) %}
{{ macros.log('file', 'config_zypp_minimal') }}
config_zypp_minimal:
  file.append:
    - name: /mnt/etc/zypp/zypp.conf
    - text:
        - solver.onlyRequires = true
        - rpm.install.excludedocs = yes
        - multiversion =
{% endif %}
