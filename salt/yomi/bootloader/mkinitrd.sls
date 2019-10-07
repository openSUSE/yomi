{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}
{% set software = pillar['software'] %}

{{ macros.log('cmd', 'mkinitrd') }}
mkinitrd:
  cmd.run:
    - name: mkinitrd -b /boot
    - root: /mnt
    - onchanges:
      - pkg: install_packages
{# TODO: Remove the double check (SumaForm bug) #}
{% if software.get('image', {}).get('url') %}
  {% for device, info in filesystems.items() %}
    {% if info.get('mountpoint') == '/' %}
      - images: dump_image_into_{{ device }}
    {% endif %}
  {% endfor %}
{% endif %}
