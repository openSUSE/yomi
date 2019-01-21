{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% set fs_file = '/mnt'|path_join('.snapshots') %}
{{ macros.log('mount', 'umount_' ~ fs_file) }}
umount_{{ fs_file }}:
  mount.unmounted:
    - name: {{ fs_file }}
    - requires: mount_{{ fs_file }}
