{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.filesystem == 'btrfs' and info.get('subvolumes') %}
    {# TODO(aplanas) is prefix optional? #}
    {% set prefix = info.subvolumes.get('prefix', '') %}
    {% if prefix %}
{{ macros.log('btrfs', 'subvol_create_' ~ device ~ '_prefix') }}
subvol_create_{{ device }}_prefix:
  btrfs.subvolume_created:
    - name: '{{ prefix }}'
    - device: {{ device }}
    - set_default: True
    - force_set_default: False
    {% endif %}

    {% for subvol in info.subvolumes.subvolume %}
      {% if prefix %}
        {% set path = prefix|path_join(subvol.path) %}
      {% else %}
        {% set path = subvol.path %}
      {% endif %}
{{ macros.log('btrfs', 'subvol_create_' ~ device ~ subvol.path) }}
subvol_create_{{ device }}_{{ subvol.path }}:
  btrfs.subvolume_created:
    - name: '{{ path }}'
    - device: {{ device }}
    - copy_on_write: {{ subvol.get('copy_on_write', True) }}
    {% endfor %}
  {% endif %}
{% endfor %}
