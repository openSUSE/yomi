{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.filesystem == 'btrfs' and info.get('subvolumes') %}
    {% set prefix = info.subvolumes.get('prefix', '') %}
    {% for subvol in info.subvolumes.subvolume %}
      {% set fs_file = '/mnt'|path_join(subvol.path) %}
umount_{{ fs_file }}:
  mount.unmounted:
    - name: {{ fs_file }}
    - requires: mount_{{ fs_file }}
    {% endfor %}
  {% endif %}

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
umount_root_mount_fstab:
  mount.unmounted:
    - name: /mnt
    - requires: mount_root_mount_fstab
  {% endif %}
{% endfor %}
