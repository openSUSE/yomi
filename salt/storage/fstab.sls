{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
mount_root_partition_fstab:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: False

create_fstab:
  file.managed:
    - name: /mnt/etc/fstab
    - source: salt://storage/etc/fstab.jinja
    - user: root
    - group: root
    - mode: 644
    - template: jinja
    - makedirs: True
    - dir_mode: 755
    - requires: mount_root_partition_software

umount_root_partition_fstab:
  mount.unmounted:
    - name: /mnt
    - requires: mount_root_partition_fstab
  {% endif %}
{% endfor %}
