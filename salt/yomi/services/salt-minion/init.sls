{% import 'macros.yml' as macros %}

{% set salt_minion = pillar['salt-minion'] %}

{% if salt_minion.get('configure') %}
{{ macros.log('module', 'create_salt-minion') }}
create_salt-minion:
  module.run:
    - file.copy:
      - src: /etc/salt
      - dst: /mnt/etc/salt
      - recurse: yes
      - remove_existing: yes
    - unless: "[ -e /mnt/etc/salt/pki/minion/minion.pem ]"
{% endif %}
