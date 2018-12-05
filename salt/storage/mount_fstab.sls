{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
mount_root_mount_fstab:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: False
  {% endif %}
{% endfor %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') and info.mountpoint != '/' %}
    {% set fs_file = '/mnt'|path_join(info.mountpoint[1:] if info.mountpoint.startswith('/') else info.mountpoint) %}
mount_{{ fs_file }}:
  mount.mounted:
    - name: {{ fs_file }}
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: False
  {% endif %}

  {% if info.filesystem == 'btrfs' and info.get('subvolumes') %}
    {% set prefix = info.subvolumes.get('prefix', '') %}
    {% for subvol in info.subvolumes.subvolume %}
      {% set fs_file = '/mnt'|path_join(subvol.path) %}
      {% set fs_mntops = 'subvol=%s'|format('/'|path_join(prefix, subvol.path)) %}
      {% if not subvol.get('copy_on_write', True) %}
        {% set fs_mntops = fs_mntops ~ ',nodatacow' %}
      {% endif %}
mount_{{ fs_file }}:
  mount.mounted:
    - name: {{ fs_file }}
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - opts: {{ fs_mntops }}
    - persist: False
    {% endfor %}
  {% endif %}
{% endfor %}
