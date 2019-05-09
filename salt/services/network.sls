{% import 'macros.yml' as macros %}

{% set interface = salt.network.interfaces() | select('!=', 'lo') | first %}

{{ macros.log('file', 'create_ifcfg_' ~ interface) }}
create_ifcfg_{{ interface }}:
  file.append:
    - name: /mnt/etc/sysconfig/network/ifcfg-{{ interface }}
    - text:
        - BOOTPROTO='dhcp'
        - MTU=''
        - REMOTE_IPADDR=''
        - STARTMODE='onboot'
