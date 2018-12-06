{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') and info.mountpoint != '/' %}
    {% set fs_file = '/mnt'|path_join(info.mountpoint[1:] if info.mountpoint.startswith('/') else info.mountpoint) %}
umount_{{ fs_file }}:
  mount.unmounted:
    - name: {{ fs_file }}
    - requires: mount_{{ fs_file }}
  {% endif %}
{% endfor %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
umount_/mnt:
  mount.unmounted:
    - name: /mnt
    - requires: mount_/mnt
  {% endif %}
{% endfor %}
