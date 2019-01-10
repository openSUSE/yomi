{% set config = pillar['config'] %}
{% set is_uefi = grains['efi'] %}
{% set is_secure_boot = grains['efi-secure-boot'] %}

install_grub2:
  pkg.installed:
    - pkgs:
      - grub2
{% if config.get('grub2_theme', False) %}
      - grub2-branding-openSUSE
{% endif %}
{% if is_uefi %}
      - grub2-x86_64-efi
  {% if is_secure_boot %}
      - shim
  {% endif %}
{% endif %}
    - no_recommends: yes
    - root: /mnt
    - require:
      - mount: mount_/mnt
