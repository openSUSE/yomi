{% set config = pillar['config'] %}
{% set partitions = pillar['partitions'] %}
{% set filesystems = pillar['filesystems'] %}
{% set bootloader = pillar['bootloader'] %}
{% set software = pillar['software'] %}

{% set label = partitions.get('config', {}).get('label', 'msdos') %}
{% for device, info in partitions.devices.items() %}
create_disk_label_{{ device }}:
  partitioned.labeled:
    - name: {{ device }}
    - label: {{ info.label|default(label) }}

  {% set size_ns = namespace(end_size=0) %}
  {% for partition in info.get('partitions', []) %}
    # TODO(aplanas) When moving it to Python, the partition number will be
    # deduced, so the require section in mkfs_partition will fail
    {% set device = device ~ info.get('number', loop.index) %}
create_partition_{{ device }}:
  partitioned.mkparted:
    - name: {{ device }}
    # TODO(aplanas) If msdos we need to create extended and logical
    - part_type: primary
    - fs_type: {{ {'swap': 'linux-swap', 'linux': 'ext2'}[partition.type] }}
    - start: {{ size_ns.end_size }}MB
    - end: {{ size_ns.end_size + partition.size }}MB
    {% set size_ns.end_size = size_ns.end_size + partition.size %}
  {% endfor %}
{% endfor %}

{% for device, info in filesystems.items() %}
mkfs_partition_{{ device }}:
  formatted.formatted:
    - name: {{ device }}
    - fs_type: {{ info.filesystem }}
    - require:
      - partitioned: create_partition_{{ device }}

  {% if info.get('mountpoint') == '/' %}
mount_root_partition_{{ device }}:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: False
    - require:
      - formatted: mkfs_partition_{{ device }}

add_install_repo_{{ device }}:
  pkgrepo.managed:
    - name: repo-oss
    - baseurl: {{ software.repo }}
    - refresh: yes
    - gpgautoimport: yes
    - root: /mnt
    - require:
      - mount: mount_root_partition_{{ device }}

install_root_partition_{{ device }}:
  pkg.installed:
    - pkgs: {{ software.packages }}
    - no_recommends: yes
    - root: /mnt
    - require:
        - pkgrepo: add_install_repo_{{ device }}

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

    {% for user in software.users %}
create_user_{{ user.username }}:
  module.run:
    - user.add:
      - name: {{ user.username }}
      - createhome: yes
      - root: /mnt
    - unless: grep -q '{{ user.username }}' /mnt/etc/shadow

update_user_{{ user.username }}:
  module.run:
    - shadow.set_password:
      - name: {{ user.username }}
      - password: {{ user.password }}
      - use_usermod: yes
      - root: /mnt
    - unless: grep -q '{{ user.username }}:{{ user.password }}' /mnt/etc/shadow
    {% endfor %}

umount_root_partition_{{ device }}:
  mount.unmounted:
    - name: /mnt
    - requires: mount_root_partition_{{ device }}
  {% endif %}
{% endfor %}

# Reboot via kexec
{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
mount_root_partition_kexec:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: False

grub_command_line:
  cmd.run:
    - name: grep -m 1 -E '^[[:space:]]*linux[[:space:]]+[^[:space:]]+vmlinuz.*$' /mnt/boot/grub2/grub.cfg | cut -d ' ' -f 2- > /tmp/command_line
    - create: /tmp/command_line

prepare_kexec:
  cmd.run:
    - name: kexec -l --initrd /mnt/boot/initrd --command-line=`cat /tmp/command_line` /mnt/boot/vmlinuz
    - onlyif: "[ -e /tmp/command_line ]"

execute_kexec:
  cmd.run:
    - name: kexec -e
  {% endif %}
{% endfor %}
