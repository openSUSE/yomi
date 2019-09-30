{% set filesystems = pillar['filesystems'] %}

{% set ns = namespace(installed=False) %}
{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
    {% if salt.cmd.run('findmnt --list --noheadings --output SOURCE /') == device %}
      {% set ns.installed = True %}
    {% endif %}
  {% endif %}
{% endfor %}

{% if not ns.installed %}
include:
  - .storage
  - .software
  - .users
  - .bootloader
  - .services
  - .post_install
  - .reboot
{% endif %}
