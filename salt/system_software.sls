{% set software = pillar['software'] %}

{% for name, repo in software.repositories.items() %}
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

install_packages:
  pkg.installed:
    - pkgs: {{ software.packages }}
    - no_recommends: yes
    - root: /mnt
