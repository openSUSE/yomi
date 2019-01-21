{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
{{ macros.log('mount', 'mount_create_fstab') }}
mount_create_fstab:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: False

{{ macros.log('file', 'create_fstab') }}
create_fstab:
  file.managed:
    - name: /mnt/etc/fstab
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - dir_mode: 755
    - replace: False
    - requires: mount_create_fstab

{{ macros.log('mount', 'umount_create_fstab') }}
umount_create_fstab:
  mount.unmounted:
    - name: /mnt
    - requires: mount_create_fstab
  {% endif %}
{% endfor %}
