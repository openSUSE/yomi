{% import 'macros.yml' as macros %}

{% set software = pillar['software'] %}

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
