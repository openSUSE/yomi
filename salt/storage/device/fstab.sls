{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
{{ macros.log('mount', 'mount_device_fstab') }}
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
{{ macros.log('mount', 'add_fstab_' ~ fs_file) }}
add_fstab_{{ fs_file }}:
  mount.fstab_present:
    - name: {{ device }}
    - fs_file: {{ fs_file }}
    - fs_vfstype: {{ info.filesystem }}
    - fs_mntops: defaults
    - fs_freq: 0
    - fs_passno: 0
  {% if not salt.filters.is_lvm(device) %}
    - mount_by: uuid
  {% endif %}
    - config: /mnt/etc/fstab
    - require:
      - mount: mount_device_fstab
{% endfor %}

{{ macros.log('mount', 'umount_device_fstab') }}
umount_device_fstab:
  mount.unmounted:
    - name: /mnt
    - requires: mount_device_fstab
