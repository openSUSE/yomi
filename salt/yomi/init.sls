{% set filesystems = pillar['filesystems'] %}

{% set installed = False %}
{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
    {% if salt.cmd.run('findmnt --list --noheadings --output SOURCE /') == device %}
      {% set installed = True %}
    {% endif %}
  {% endif %}
{% endfor %}

{% if not installed %}
include:
  - .storage
  - .software
  - .users
  - .bootloader
  - .services
  - .post_install
  - .reboot
{% endif %}
