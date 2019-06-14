{% import 'macros.yml' as macros %}

{{ macros.log('pkg', 'install_salt-minion') }}
install_salt-minion:
  pkg.installed:
    - name: salt-minion
    - no_recommends: yes
    - root: /mnt
    - require:
      - mount: mount_/mnt
