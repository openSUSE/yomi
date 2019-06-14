{% import 'macros.yml' as macros %}

{% set users = pillar['users'] %}

{% for user in users %}
{{ macros.log('module', 'create_user_' ~ user.username) }}
create_user_{{ user.username }}:
  module.run:
    - user.add:
      - name: {{ user.username }}
      - createhome: yes
      - root: /mnt
    - unless: grep -q '{{ user.username }}' /mnt/etc/shadow

{{ macros.log('module', 'update_user_' ~ user.username) }}
update_user_{{ user.username }}:
  module.run:
    - shadow.set_password:
      - name: {{ user.username }}
      - password: {{ user.password }}
      - use_usermod: yes
      - root: /mnt
    - unless: grep -q '{{ user.username }}:{{ user.password }}' /mnt/etc/shadow
{% endfor %}
