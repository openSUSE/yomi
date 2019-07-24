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

  {% if user.get('password') %}
{{ macros.log('module', 'set_password_user_' ~ user.username) }}
set_password_user_{{ user.username }}:
  module.run:
    - shadow.set_password:
      - name: {{ user.username }}
      - password: {{ user.password }}
      - use_usermod: yes
      - root: /mnt
    - unless: grep -q '{{ user.username }}:{{ user.password }}' /mnt/etc/shadow
  {% endif %}

  {% for certificate in user.get('certificates', []) %}
{{ macros.log('module', 'add_certificate_user_' ~ user.username ~ '_' ~ loop.index) }}
add_certificate_users_{{ user.username }}_{{ loop.index }}:
  module.run:
    - chroot.call:
      - root: /mnt
      - function: ssh.set_auth_key
      - user: {{ user.username }}
      - key: '{{ certificate }}'
    - unless: grep -q '{{ certificate }}' /mnt/{{ 'home/' if user.username != 'root' else '' }}{{ user.username }}/.ssh/authorized_keys
  {% endfor %}
{% endfor %}
