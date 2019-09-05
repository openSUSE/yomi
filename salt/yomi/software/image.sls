{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}
{% set software = pillar['software'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
{{ macros.log('module', 'dump_image_into_' ~ device) }}
dump_image_into_{{ device }}:
  images.dumped:
    - name: {{ software.image.url }}
    - device: {{ device }}
    {% for checksum_type in ('md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512') %}
      {% if checksum_type in software.image %}
    - checksum_type: {{ checksum_type }}
    - checksum: {{ software.image[checksum_type] or '' }}
      {% endif %}
    {% endfor %}

{{ macros.log('mount', 'mount_image_/mnt') }}
mount_image_/mnt:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: no

{{ macros.log('cmd', 'generate_machine_id_' ~ device) }}
generate_machine_id_{{ device }}:
  cmd.run:
    - name: systemd-machine-id-setup
    - root: /mnt
    - creates: /mnt/etc/machine-id

{{ macros.log('mount', 'umount_image_/mnt') }}
umount_/mnt:
  mount.unmounted:
    - name: /mnt
    - requires: mount_image_/mnt
  {% endif %}
{% endfor %}
