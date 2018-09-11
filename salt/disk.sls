{% set storage = pillar['storage'] %}
{% set install = pillar['install'] %}

parted:
  pkg.installed

xfsprogs:
  pkg.installed

btrfsprogs:
  pkg.installed

{% for disk_name, disk in storage.disk.items() %}
  {% set disk_name = disk.name|default(disk_name) %}
create_disk_label_{{ disk_name }}:
  module.run:
    - name: partition.mklabel
    - device: {{ disk_name }}
    - label_type: {{ disk.get('type', 'msdos') }}
    - unless: "fdisk -l {{ disk_name }} | grep -i 'Disklabel type: {{ disk.get('type', 'dos') }}'"
    - require:
      - pkg: parted

  {% set size_ns = namespace(end_size=0) %}
  {% if disk.get('startsector', None) %}
    # TODO(aplanas): if startsector is set, we cannot use MB as units
    {% set size_ns.end_size = disk.get('startsector')|int %}
  {% endif %}

  {% for partition in disk.get('partitions', []) %}
create_partition_{{ disk_name }}_{{ loop.index }}:
  module.run:
    - name: partition.mkpart
    - device: {{ disk_name }}
    - part_type: primary
    {% if partition.type is defined %}
      # NOTE(aplanas): for parted we only takes care of type 83 and
      # 82, the file system will come later
      # TODO(aplanas): evaluate drop `type` for an enum ([fs], swap)
      # Also note that this is wrong, as LVM or RAID another types are
      # used and have different types IDs
      {% if partition.type == 'linux-swap' %}
        {% set partition_type = partition.type %}
      {% else %}
        {% set partition_type = 'ext2' %}
      {% endif %}      
    - fs_type: {{ partition_type }}
    {% endif %}
    - start: {{ size_ns.end_size }}MB
    - end: {{ size_ns.end_size + partition.size }}MB
    - unless: "blkid {{ disk_name }}{{ loop.index }} {{ disk_name }}p{{ loop.index }}"
    - require:
      - module: create_disk_label_{{ disk_name }}
    {% set size_ns.end_size = size_ns.end_size + partition.size %}
  {% endfor %}

probe_partions_{{ disk_name }}:
  module.run:
    - name: partition.probe
    - devices:
      - {{ disk_name }}

  {% for partition in disk.get('partitions', []) %}
mkfs_partition_{{ disk_name }}_{{ loop.index }}:
    {% if partition.get("type", "ext3") == "linux-swap" %}
  cmd.run:
    - name: "mkswap {{ disk_name }}{{ loop.index }}"
    - unless: "file -L -s {{ disk_name }}{{ loop.index }} | grep -q 'swap file'"
    {% else %}
  blockdev.formatted:
    - name: {{ disk_name }}{{ loop.index }}
    - fs_type: {{ partition.get("type", "ext3") }}
    - require:
      - module: create_partition_{{ disk_name }}_{{ loop.index }}
    {% endif %}

    {% if partition.get("mountpoint", None)  == "/" %}
mount_root_partition_{{ disk_name }}{{ loop.index }}:
  mount.mounted:
    - name: /mnt
    - device: {{ disk_name }}{{ loop.index }}
    - fstype: {{ partition.get("type", "ext3") }}
    - persist: False

/mnt/etc/zypp/repos.d/:
  file.directory:
    - user: root
    - group: root
    - dir_mode: 755
    - recurse:
      - user
      - group
      - mode
    - makedirs: True
    - requires: mount_root_partition_{{ disk_name }}{{ loop.index }}

add_install_repo:
  cmd.run:
    - name: zypper --root /mnt ar -f "{{ install.repo }}" repo-oss
    - creates: /mnt/etc/zypp/repos.d/repo-oss.repo
    - requires: /mnt/etc/zypp/repos.d/

refresh_install_repo:
  cmd.run:
    - name: zypper --root /mnt --gpg-auto-import-keys refresh
    - creates: /mnt/var/cache/zypp/raw/repo-oss

install_root_partition_{{ disk_name }}{{ loop.index }}:
  cmd.run:
    - name: zypper --root /mnt --non-interactive install --no-recommends --auto-agree-with-licenses {{ install.packages|join(' ') }}
    - creates: /mnt/usr/share/doc/packages/paterns/base.txt
    - requires: refresh_install_repo

mkinitrd:
  cmd.run:
    - name: mkinitrd -d /mnt -b /mnt/boot
    - onlyif: "[ ! -e /mnt/boot/initrd ]"

      {% for user in install.users %}
create_user_{{ user.username }}:
  cmd.run:
    - name: useradd --prefix /mnt --create-home {{ user.username }}
    - unless: grep {{ user.username }} /mnt/etc/shadow

update_user_{{ user.username }}:
  cmd.run:
    - name: usermod --prefix /mnt --password '{{ user.password }}' {{ user.username }}
    - onlyif: grep {{ user.username }} /mnt/etc/shadow
      {% endfor %}

/mnt/proc:
  mount.mounted:
    - device: proc
    - fstype: proc
    - persist: False

/mnt/sys:
  mount.mounted:
    - device: sys
    - fstype: sysfs
    - persist: False

/mnt/dev:
  mount.mounted:
    - device: /dev
    - fstype: none
    - opts: bind
    - persist: False

grub2_mkconfig_chroot:
   cmd.run:
     - name: chroot /mnt grub2-mkconfig -o /boot/grub2/grub.cfg
     - creates: /mnt/boot/grub2/grub.cfg
     - requires:
       - /mnt/proc
       - /mnt/sys
       - /mnt/dev

grub2_install:
   cmd.run:
     - name: grub2-install --boot-directory=/mnt/boot {{ disk_name }} --force
     - requires:
       - grub2_mkconfig_chroot:

umount_/mnt/dev:
  mount.unmounted:
    - name: /mnt/dev

umount_/mnt/sys:
  mount.unmounted:
    - name: /mnt/sys

umount_/mnt/proc:
  mount.unmounted:
    - name: /mnt/proc

umount_root_partition_{{ disk_name }}{{ loop.index }}:
  mount.unmounted:
    - name: /mnt
    - requires: mount_root_partition_{{ disk_name }}{{ loop.index }}
    {% endif %}
  {% endfor %}
{% endfor %}

# Reboot via kexec
{% for partition in disk.get('partitions', []) %}
  {% if partition.get("mountpoint", None)  == "/" %}
mount_root_partition_{{ disk_name }}{{ loop.index }}:
  mount.mounted:
    - name: /mnt
    - device: {{ disk_name }}{{ loop.index }}
    - fstype: {{ partition.get("type", "ext3") }}
    - persist: False

    {% set cmdline = salt['cmd.run']("grep -E '^[[:space:]]*linux[[:space:]]+[^[:space:]]+vmlinux.*$' | cut -d ' ' -f 2-") %}

prepare_kexec_for_{{ disk_name }}{{ loop.index }}:
  cmd.run:
    - name: kexec -l --initrd /mnt/boot/initrd --command-line="{{ cmdline }}" /mnt/boot/vmlinuz

execute_kexec_for_{{ disk_name }}{{ loop.index }}:
  cmd.run:
    - name: kexec -e
  {% endif %}
{% endfor %}
