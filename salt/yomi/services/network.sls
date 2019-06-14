{% import 'macros.yml' as macros %}

{% set interfaces = salt.network.interfaces() | select('!=', 'lo') %}

{% for interface in interfaces %}
{{ macros.log('file', 'create_ifcfg_' ~ interface) }}
create_ifcfg_{{ interface }}:
  file.append:
    - name: /mnt/etc/sysconfig/network/ifcfg-{{ interface }}
    - text:
        - BOOTPROTO='dhcp'
        - MTU=''
        - REMOTE_IPADDR=''
        - STARTMODE='onboot'
{% endfor %}
