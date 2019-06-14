{% set config = pillar['config'] %}

include:
  - .mkinitrd
  - .grub2_mkconfig
  - .grub2_install
