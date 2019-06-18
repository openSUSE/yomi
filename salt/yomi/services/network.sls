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

{{ macros.log('file', 'dhcp_hostname') }}
dhcp_hostname:
  file.append:
    - name: /mnt/etc/sysconfig/dhcp
    - text:
        - DHCLIENT_SET_HOSTNAME="yes"
        - WRITE_HOSTNAME_TO_HOSTS="no"
