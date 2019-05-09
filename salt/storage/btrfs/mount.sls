{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.filesystem == 'btrfs' and info.get('subvolumes') %}
    {% set prefix = info.subvolumes.get('prefix', '') %}
    {% for subvol in info.subvolumes.subvolume %}
      {% set fs_file = '/mnt'|path_join(subvol.path) %}
      {% set fs_mntops = 'subvol=%s'|format('/'|path_join(prefix, subvol.path)) %}
      {% if not subvol.get('copy_on_write', True) %}
        {% set fs_mntops = fs_mntops ~ ',nodatacow' %}
      {% endif %}
{{ macros.log('mount', 'mount_' ~ fs_file) }}
mount_{{ fs_file }}:
  mount.mounted:
    - name: {{ fs_file }}
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - mkmnt: yes
    - opts: {{ fs_mntops }}
    - persist: no
    {% endfor %}
  {% endif %}
{% endfor %}
