{% set software = pillar['software'] %}

include:
{% if 'image' in software %}
  - .image
  - ..storage.fstab
  - ..storage.mount
{% endif %}
  - .pkgmanager
  - ..storage.software
  - ..bootloader.software
  - ..services.software
  - ..chroot.software
