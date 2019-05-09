{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
{{ macros.log('mount', 'mount_snapper_fstab') }}
mount_snapper_fstab:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: no
  {% endif %}
{% endfor %}

{% for device, info in filesystems.items() %}
  {% if info.filesystem == 'btrfs' and info.mountpoint == '/' %}
    {% set prefix = info.subvolumes.get('prefix', '') %}
    {% set fs_file = '/'|path_join('.snapshots') %}
    {% set fs_mntops = 'subvol=%s'|format('/'|path_join(prefix, '.snapshots')) %}
{{ macros.log('mount', 'add_fstab_' ~ fs_file) }}
add_fstab_{{ fs_file }}:
  mount.fstab_present:
    - name: {{ device }}
    - fs_file: {{ fs_file }}
    - fs_vfstype: {{ info.filesystem }}
    - fs_mntops: {{ fs_mntops }}
    - fs_freq: 0
    - fs_passno: 0
    {% if not salt.filters.is_lvm(device) %}
    - mount_by: uuid
    {% endif %}
    - config: /mnt/etc/fstab
    - require:
      - mount: mount_snapper_fstab
  {% endif %}
{% endfor %}

{{ macros.log('mount', 'umount_snapper_fstab') }}
umount_snapper_fstab:
  mount.unmounted:
    - name: /mnt
    - requires: mount_snapper_fstab
