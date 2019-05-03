{% import 'macros.yml' as macros %}

{% set net_name = salt.devices.net_name('lan0') %}

{{ macros.log('file', 'create_ifcfg_' ~ net_name) }}
create_ifcfg_{{ net_name }}:
  file.append:
    - name: /mnt/etc/sysconfig/network/ifcfg-{{ net_name }}
    - text:
        - BOOTPROTO='dhcp'
        - MTU=''
        - REMOTE_IPADDR=''
        - STARTMODE='onboot'
