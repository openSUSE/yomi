{% set config = pillar['config'] %}

include:
  - .bootloader.mkinitrd
  - .bootloader.grub2-mkconfig
  - .bootloader.grub2-install
