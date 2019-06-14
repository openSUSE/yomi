{% import 'macros.yml' as macros %}

{{ macros.log('cmd', 'mkinitrd') }}
mkinitrd:
  cmd.run:
    - name: mkinitrd -d /mnt -b /mnt/boot
    - creates: /mnt/boot/initrd
