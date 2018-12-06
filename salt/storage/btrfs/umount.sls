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
{% endfor %}
