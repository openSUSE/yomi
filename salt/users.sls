{% set filesystems = pillar['filesystems'] %}
{% set users = pillar['users'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
mount_root_partition_users:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: False

    {% for user in users %}
create_user_{{ user.username }}:
  module.run:
    - user.add:
      - name: {{ user.username }}
      - createhome: yes
      - root: /mnt
    - unless: grep -q '{{ user.username }}' /mnt/etc/shadow

update_user_{{ user.username }}:
  module.run:
    - shadow.set_password:
      - name: {{ user.username }}
      - password: {{ user.password }}
      - use_usermod: yes
      - root: /mnt
    - unless: grep -q '{{ user.username }}:{{ user.password }}' /mnt/etc/shadow
    {% endfor %}

umount_root_partition_users:
  mount.unmounted:
    - name: /mnt
    - requires: mount_root_partition_users
  {% endif %}
{% endfor %}
