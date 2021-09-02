{% import 'macros.yml' as macros %}

{% set salt_minion = pillar['salt-minion'] %}

{% if salt_minion.get('config') %}
{{ macros.log('module', 'synchronize_salt-minion_etc') }}
synchronize_salt-minion_etc:
  module.run:
    - file.copy:
      - src: /etc/salt
      - dst: /mnt/etc/salt
      - recurse: yes
      - remove_existing: yes
    - unless: "[ -e /mnt/etc/salt/pki/minion/minion.pem ]"

{{ macros.log('module', 'synchronize_salt-minion_var') }}
synchronize_salt-minion_var:
  module.run:
    - file.copy:
      - src: /var/cache/salt
      - dst: /mnt/var/cache/salt
      - recurse: yes
      - remove_existing: yes
    - unless: "[ -e /mnt/var/cache/salt/minion/extmods ]"

{{ macros.log('file', 'clean_salt-minion_var') }}
clean_salt-minion_var:
  file.tidied:
    - name: /mnt/var/cache/salt/minion
    - matches:
      - ".*\\.pyc"
      - "\\d+"
{% endif %}
