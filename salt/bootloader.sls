{% set filesystems = pillar['filesystems'] %}
{% set bootloader = pillar['bootloader'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
mount_root_partition_bootloader:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: False

mkinitrd_{{ device }}:
  cmd.run:
    - name: mkinitrd -d /mnt -b /mnt/boot
    - creates: /mnt/boot/initrd

grub2_mkconfig_chroot:
  cmd.run:
    - name: grub2-mkconfig -o /boot/grub2/grub.cfg
    - root: /mnt
    - creates: /mnt/boot/grub2/grub.cfg

grub2_install:
  cmd.run:
    - name: grub2-install --boot-directory=/mnt/boot {{ bootloader.device }} --force
    - require:
      - cmd: grub2_mkconfig_chroot
    - unless: file -s {{ bootloader.device }} | grep -q 'DOS/MBR boot sector'

umount_root_partition_bootloader:
  mount.unmounted:
    - name: /mnt
    - requires: mount_root_partition_bootloader
  {% endif %}
{% endfor %}
