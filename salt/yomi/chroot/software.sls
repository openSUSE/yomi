{% import 'macros.yml' as macros %}

{{ macros.log('module', 'freeze_chroot') }}
freeze_chroot:
  module.run:
    - freezer.freeze:
      - name: yomi-chroot
      - includes: [pattern]
      - root: /mnt
    - unless: "[ -e /var/cache/salt/minion/freezer/yomi-chroot-pkgs.yml ]"

{{ macros.log('pkg', 'install_python3-base') }}
install_python3-base:
  pkg.installed:
    - name: python3-base
    - no_recommends: yes
    - root: /mnt
    - require:
      - mount: mount_/mnt
