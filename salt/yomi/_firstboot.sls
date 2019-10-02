{% import 'macros.yml' as macros %}

{% set config = pillar['config'] %}

{{ macros.log('module', 'systemd_firstboot') }}
systemd_firstboot:
  module.run:
    - service.firstboot:
      - locale: {{ config.get('locale', 'en_US.utf8') }}
{% if config.get('locale_messages') %}
      - locale_message: {{ config['locale_messages'] }}
{% endif %}
      - keymap: {{ config.get('keymap', 'us') }}
      - timezone: {{ config.get('timezone', 'UTC') }}
{% if config.get('hostname') %}
      - hostname: {{ config['hostname'] }}
{% endif %}
{% if config.get('machine_id') %}
      - machine_id: {{ config['machine_id'] }}
{% endif %}
      - root: /mnt
    - creates:
        - /mnt/etc/hostname
        - /mnt/etc/locale.conf
        - /mnt/etc/localtime
        - /mnt/etc/machine-id
        - /mnt/etc/vconsole.conf

{% if not config.get('machine_id') %}
{{ macros.log('module', 'create_machine-id') }}
create_machine-id:
  module.run:
    - file.copy:
      - src: /etc/machine-id
      - dst: /mnt/etc/machine-id
      - remove_existing: yes
{% endif %}
