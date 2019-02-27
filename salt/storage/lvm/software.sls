{% import 'macros.yml' as macros %}

{{ macros.log('pkg', 'install_lvm2') }}
install_lvm2:
  pkg.installed:
    - name: lvm2
    - no_recommends: yes
    - root: /mnt
    - require:
      - mount: mount_/mnt
