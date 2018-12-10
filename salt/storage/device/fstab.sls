{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
mount_device_fstab:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: False
  {% endif %}
{% endfor %}

{% for device, info in filesystems.items() %}
  {% set fs_file = 'swap' if info.filesystem == 'swap' else info.mountpoint %}
add_fstab_{{ fs_file }}:
  mount.fstab_present:
    - name: {{ device }}
    - fs_file: {{ fs_file }}
    - fs_vfstype: {{ info.filesystem }}
    - fs_mntops: defaults
    - fs_freq: 0
    - fs_passno: 0
    - mount_by: uuid
    - config: /mnt/etc/fstab
    - require:
      - mount: mount_device_fstab
{% endfor %}

umount_device_fstab:
  mount.unmounted:
    - name: /mnt
    - requires: mount_device_fstab
