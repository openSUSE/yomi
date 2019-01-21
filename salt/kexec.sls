{% import 'macros.yml' as macros %}

{% set filesystems = pillar['filesystems'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
{{ macros.log('mount', 'mount_root_partition_kexec') }}
mount_root_partition_kexec:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: False

{{ macros.log('cmd', 'grub_command_line') }}
grub_command_line:
  cmd.run:
    - name: grep -m 1 -E '^[[:space:]]*linux[[:space:]]+[^[:space:]]+vmlinuz.*$' /mnt/boot/grub2/grub.cfg | cut -d ' ' -f 2 > /tmp/command_line
    - create: /tmp/command_line

{{ macros.log('cmd', 'prepare_kexec') }}
prepare_kexec:
  cmd.run:
    - name: kexec -l --initrd /mnt/boot/initrd --command-line=`cat /tmp/command_line` /mnt/boot/vmlinuz
    - onlyif: "[ -e /tmp/command_line ]"

{{ macros.log('cmd', 'execute_kexec') }}
execute_kexec:
  cmd.run:
    - name: kexec -e
  {% endif %}
{% endfor %}
