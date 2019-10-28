{% import 'macros.yml' as macros %}

{% set config = pillar['config'] %}
{% set reboot = config.get('reboot', True) %}

{% if reboot == 'kexec' %}
{{ macros.log('cmd', 'grub_command_line') }}
grub_command_line:
  cmd.run:
    - name: grep -m 1 -E '^[[:space:]]*linux(efi)?[[:space:]]+[^[:space:]]+vmlinuz.*$' /mnt/boot/grub2/grub.cfg | cut -d ' ' -f 2-3 > /tmp/command_line
    - create: /tmp/command_line

{{ macros.log('cmd', 'prepare_kexec') }}
prepare_kexec:
  cmd.run:
    - name: kexec -a -l /mnt/boot/vmlinuz --initrd=/mnt/boot/initrd --command-line="$(cat /tmp/command_line)"
    - onlyif: "[ -e /tmp/command_line ]"

{{ macros.log('cmd', 'execute_kexec') }}
execute_kexec:
  cmd.run:
    - name: systemctl kexec

{% elif reboot == 'halt' %}
{{ macros.log('module', 'halt') }}
halt:
  module.run:
    - system.halt:

{% elif reboot == 'shutdown' %}
{{ macros.log('module', 'shutdown') }}
shutdown:
  module.run:
    - system.shutdown:

{% elif reboot %}
{{ macros.log('module', 'reboot') }}
reboot:
  module.run:
    - system.reboot:
{% endif %}
