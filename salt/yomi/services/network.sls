{% import 'macros.yml' as macros %}

{% set interfaces = salt.network.interfaces() | select('!=', 'lo') %}

{% for interface in interfaces %}
{{ macros.log('file', 'create_ifcfg_' ~ interface) }}
create_ifcfg_{{ interface }}:
  file.append:
    - name: /mnt/etc/sysconfig/network/ifcfg-{{ interface }}
    - text:
        - BOOTPROTO='dhcp'
        - BROADCAST=''
        - ETHTOOL_OPTIONS=''
        - IPADDR=''
        - MTU=''
        - NAME=''
        - NETMASK=''
        - NETWORK=''
        - REMOTE_IPADDR=''
        - STARTMODE='auto'
{% endfor %}
