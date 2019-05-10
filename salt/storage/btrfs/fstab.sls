{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
{{ macros.log('mount', 'mount_btrfs_fstab') }}
mount_btrfs_fstab:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: no
  {% endif %}
{% endfor %}

{% for device, info in filesystems.items() %}
  {% if info.filesystem == 'btrfs' and info.get('subvolumes') %}
    {% set prefix = info.subvolumes.get('prefix', '') %}
    {% for subvol in info.subvolumes.subvolume %}
      {% set fs_file = '/'|path_join(subvol.path) %}
      {% set fs_mntops = 'subvol=%s'|format('/'|path_join(prefix, subvol.path)) %}
      {% if not subvol.get('copy_on_write', True) %}
        {# TODO(aplanas) nodatacow seems optional if chattr was used #}
        {% set fs_mntops = fs_mntops ~ ',nodatacow' %}
      {% endif %}
{{ macros.log('mount', 'add_fstab' ~ '_' ~ fs_file) }}
add_fstab_{{ fs_file }}:
  mount.fstab_present:
    - name: {{ device }}
    - fs_file: {{ fs_file }}
    - fs_vfstype: {{ info.filesystem }}
    - fs_mntops: {{ fs_mntops }}
    - fs_freq: 0
    - fs_passno: 0
    - mount_by: uuid
    - not_change: yes
    - config: /mnt/etc/fstab
    - require:
      - mount: mount_btrfs_fstab
    {% endfor %}
  {% endif %}
{% endfor %}

{{ macros.log('mount', 'umount_btrfs_fstab') }}
umount_btrfs_fstab:
  mount.unmounted:
    - name: /mnt
    - requires: mount_btrfs_fstab
