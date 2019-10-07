{% set config = pillar['config'] %}

include:
  - .grub2_mkconfig
  - .grub2_install
