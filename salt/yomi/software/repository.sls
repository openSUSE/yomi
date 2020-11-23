{% import 'macros.yml' as macros %}

{% set software = pillar['software'] %}
{% set software_config = software.get('config', {}) %}

{% if software_config.get('transfer') %}
{{ macros.log('module', 'transfer_repositories') }}
migrate_repositories:
  pkgrepo.migrated:
    - name: /mnt
    - keys: yes

  {% for cert_dir in ['/usr/share/pki/trust/anchors', '/usr/share/pki/trust/blacklist',
                      '/etc/pki/trust/anchors', '/etc/pki/trust/blacklist'] %}
migrate_{{ cert_dir }}:
  module.run:
    - file.copy:
      - src: {{ cert_dir }}
      - dst: /mnt{{ cert_dir }}
      - recurse: yes
      - remove_existing: yes
    - unless: "[ -e /mnt{{ cert_dir }} ]"
  {% endfor %}
{% endif %}

# TODO: boo#1178910 - This zypper bug creates /var/lib/rpm and
# /usr/lib/sysimage/rpm independently, and not linked together
{{ macros.log('file', 'create_usr_lib_sysimage_rpm') }}
create_usr_lib_sysimage_rpm:
  file.directory:
    - name: /mnt/usr/lib/sysimage/rpm
    - makedirs: yes

{{ macros.log('file', 'symlink_var_lib_rpm') }}
symlink_var_lib_rpm:
  file.symlink:
    - name: /mnt/var/lib/rpm
    - target: ../../usr/lib/sysimage/rpm
    - makedirs: yes

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
