{% set software = pillar['software'] %}

include:
{# TODO: Remove the double check (SumaForm bug) #}
{% if software.get('image', {}).get('url') %}
  - .image
  - ..storage.fstab
  - ..storage.mount
{% endif %}
  - .repository
  - .software
{% if pillar.get('suseconnect', {}).get('config', {}).get('regcode') %}
  - .suseconnect
{% endif %}
  - ..storage.software
  - ..bootloader.software
  - ..services.software
  - ..chroot.software
