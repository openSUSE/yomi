{% import 'macros.yml' as macros %}

{{ macros.log('file', 'config_snapper_grub2') }}
config_snapper_grub2:
  file.append:
    - name: /mnt/etc/default/grub
    - text: SUSE_BTRFS_SNAPSHOT_BOOTING="true"
