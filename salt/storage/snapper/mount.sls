{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.filesystem == 'btrfs' and info.mountpoint == '/' %}
    {% set prefix = info.subvolumes.get('prefix', '') %}
    {% set fs_mntops = 'subvol=%s'|format('/'|path_join(prefix, '.snapshots')) %}
    {% set fs_file = '/mnt'|path_join('.snapshots') %}
{{ macros.log('mount', 'mount_' ~ fs_file) }}
mount_{{ fs_file }}:
  mount.mounted:
    - name: {{ fs_file }}
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - mkmnt: no
    - opts: {{ fs_mntops }}
    - persist: no
  {% endif %}
{% endfor %}
