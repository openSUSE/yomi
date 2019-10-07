{% set config = pillar['config'] %}

include:
  - ..chroot.umount
{% if config.get('snapper') %}
  - .snapper.umount
{% endif %}
  - .btrfs.umount
  - .device.umount
