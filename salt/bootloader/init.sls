{% set config = pillar['config'] %}

include:
  - .mkinitrd
  - .grub2-mkconfig
  - .grub2-install
