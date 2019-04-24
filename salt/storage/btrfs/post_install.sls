{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.filesystem == 'btrfs' and info.get('options') %}
    {% set fs_file = '/mnt'|path_join(info.mountpoint[1:] if info.mountpoint.startswith('/') else info.mountpoint) %}
    {% if 'ro' in info['options'] %}
      {# TODO(aplanas) create an state #}
{{ macros.log('cmd', 'set_property_ro_' ~ fs_file) }}
set_property_ro_{{ fs_file }}:
  cmd.run:
    - name: btrfs property set -t subvol {{ fs_file }} ro true
    - onlyif: btrfs property get -t subvol {{ fs_file }} ro | grep -q false
    {% endif %}
  {% endif %}
{% endfor %}
