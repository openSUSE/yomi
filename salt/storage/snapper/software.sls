install_snapper:
  pkg.installed:
    - pkgs:
      - snapper
      - grub2-snapper-plugin
      - snapper-zypp-plugin
    - no_recommends: yes
    - root: /mnt
    - require:
      - mount: mount_/mnt
