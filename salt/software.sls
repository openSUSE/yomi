{% set config = pillar['config'] %}

include:
  - system_software
  - .bootloader.software
{% if 'raid' in pillar %}
  - .storage.raid.software
{% endif %}
{% if 'lvm' in pillar %}
  - .storage.lvm.software
{% endif %}
{% if config.get('snapper', False) %}
  - .storage.snapper.software
{% endif %}
