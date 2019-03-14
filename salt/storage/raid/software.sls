{% import 'macros.yml' as macros %}

{{ macros.log('pkg', 'install_raid') }}
install_raid:
  pkg.installed:
    - pkgs:
      - mdadm
      - dmraid
    - no_recommends: yes
    - root: /mnt
    - require:
      - mount: mount_/mnt
