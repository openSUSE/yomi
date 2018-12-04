{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
mount_root_partition_fstab:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: False

create_fstab:
  file.managed:
    - name: /mnt/etc/fstab
    - user: root
    - group: root
    - mode: 644
    - makedirs: True
    - dir_mode: 755
    - requires: mount_root_partition_software
  {% endif %}
{% endfor %}

{% for device, info in filesystems.items() %}
  {% set fs_file = 'swap' if info.filesystem == 'swap' else info.mountpoint %}
add_fstab_entry_{{ fs_file }}:
  xmount.fstab_present:
    - name: {{ device }}
    - fs_file: {{ fs_file }}
    - fs_vfstype: {{ info.filesystem }}
    - fs_mntops: defaults
    - fs_freq: 0
    - fs_passno: 0
    - mount_by: uuid
    - config: /mnt/etc/fstab

  {% if info.filesystem == 'btrfs' and info.get('subvolumes') %}
    {% set prefix = info.subvolumes.get('prefix', '') %}
    {% for subvol in info.subvolumes.subvolume %}
      {% set fs_file = '/'|path_join(subvol.path) %}
      {% set fs_mntops = 'subvol=%s'|format('/'|path_join(prefix, subvol.path)) %}
      {% if not subvol.get('copy_on_write', True) %}
        {# TODO(aplanas) nodatacow seems optional if chattr was used #}
        {% set fs_mntops = fs_mntops ~ ',nodatacow' %}
      {% endif %}
add_fstab_subvolume_entry_{{ fs_file }}:
  xmount.fstab_present:
    - name: {{ device }}
    - fs_file: {{ fs_file }}
    - fs_vfstype: {{ info.filesystem }}
    - fs_mntops: {{ fs_mntops }}
    - fs_freq: 0
    - fs_passno: 0
    - mount_by: uuid
    - config: /mnt/etc/fstab
    {% endfor %}
  {% endif %}
{% endfor %}

umount_root_partition_fstab:
  mount.unmounted:
    - name: /mnt
    - requires: mount_root_partition_fstab
