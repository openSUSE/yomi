{% set software = pillar['software'] %}

include:
{# TODO: Remove the double check (SumaForm bug) #}
{% if software.get('image', {}).get('url') %}
  - .image
  - ..storage.fstab
  - ..storage.mount
{% endif %}
  - .pkgmanager
  - ..storage.software
  - ..bootloader.software
  - ..services.software
  - ..chroot.software
