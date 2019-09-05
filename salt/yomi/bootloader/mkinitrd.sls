{% import 'macros.yml' as macros %}

{{ macros.log('cmd', 'mkinitrd') }}
mkinitrd:
  cmd.run:
    - name: mkinitrd -b /boot
    - root: /mnt
    - creates: /mnt/boot/initrd
