{% import 'macros.yml' as macros %}

{{ macros.log('module', 'unfreeze_chroot') }}
unfreeze_chroot:
  module.run:
    - freezer.restore:
      - name: yomi-chroot
      - clean: True
      - includes: [pattern]
      - root: /mnt
    - onlyif: "[ -e /var/cache/salt/minion/freezer/yomi-chroot-pkgs.yml ]"
