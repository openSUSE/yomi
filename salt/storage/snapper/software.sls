install_snapper:
  pkg.installed:
    - name: snapper
    - no_recommends: yes
    - root: /mnt
    - require:
      - mount: mount_/mnt
