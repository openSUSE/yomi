{% import 'macros.yml' as macros %}

{% set config = pillar['config'] %}
{% set target = config.get('target', 'multi-user.target') %}

{{ macros.log('cmd', 'systemd_set_target') }}
systemd_set_target:
  cmd.run:
    - name: systemctl set-target {{ target }}
    - unless: readlink -f /mnt/etc/systemd/system/default.target | grep -q {{ target }}
    - root: /mnt
