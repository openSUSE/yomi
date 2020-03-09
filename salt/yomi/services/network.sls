{% import 'macros.yml' as macros %}

{% set interfaces = salt.network.interfaces() | select('!=', 'lo') %}

# This assume that the image used for deployment is under a
# predictable network interface name, like Tumbleweed. For SLE, boot
# the image with `net.ifnames=1`
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
    - unless: "[ -e /mnt/usr/lib/udev/rules.d/75-persistent-net-generator.rules ]"

{{ macros.log('file', 'create_ifcfg_eth' ~ loop.index0) }}
create_ifcfg_eth{{ loop.index0 }}:
  file.append:
    - name: /mnt/etc/sysconfig/network/ifcfg-eth{{ loop.index0 }}
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
    - onlyif: "[ -e /mnt/usr/lib/udev/rules.d/75-persistent-net-generator.rules ]"
{% endfor %}

{{ macros.log('file', 'dhcp_hostname') }}
dhcp_hostname:
  file.append:
    - name: /mnt/etc/sysconfig/network/dhcp
    - text:
        - DHCLIENT_SET_HOSTNAME="yes"
        - WRITE_HOSTNAME_TO_HOSTS="no"
