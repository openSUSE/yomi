{% set filesystems = pillar['filesystems'] %}

{% set fs_file = '/mnt'|path_join('.snapshots') %}
umount_{{ fs_file }}:
  mount.unmounted:
    - name: {{ fs_file }}
    - requires: mount_{{ fs_file }}
