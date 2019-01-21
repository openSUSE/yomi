{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
{{ macros.log('mount', 'mount_/mnt') }}
mount_/mnt:
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
{{ macros.log('mount', 'mount_' ~ fs_file) }}
mount_{{ fs_file }}:
  mount.mounted:
    - name: {{ fs_file }}
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - mkmnt: True
    - persist: False
  {% endif %}
{% endfor %}
