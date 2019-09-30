{% set software = pillar['software'] %}

include:
{% if software.get('image', {}) %}
  - .image
  - ..storage.fstab
  - ..storage.mount
{% endif %}
  - .pkgmanager
  - ..storage.software
  - ..bootloader.software
  - ..services.software
  - ..chroot.software
