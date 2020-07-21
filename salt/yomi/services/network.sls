{% import 'macros.yml' as macros %}

{% set interfaces = salt.network.interfaces() %}
{% set interfaces_except_lo = interfaces | select('!=', 'lo') %}

{{ macros.log('file', 'create_systemd_network_directory') }}
create_systemd_network_directory:
  file.directory:
    - name: /mnt/etc/systemd/network
    - user: root
    - group: root
    - dir_mode: 755
    - unless: "[ -e /mnt/usr/lib/udev/rules.d/75-persistent-net-generator.rules ]"

# This assume that the image used for deployment is under a
# predictable network interface name, like Tumbleweed. For SLE, boot
# the image with `net.ifnames=1`
{% for interface in interfaces_except_lo %}
{{ macros.log('file', 'create_ifcfg_ifnames_' ~ interface) }}
create_ifcfg_ifnames_{{ interface }}:
  file.append:
    - name: /mnt/etc/sysconfig/network/ifcfg-{{ interface }}
    - text: |
        BOOTPROTO='dhcp'
        BROADCAST=''
        ETHTOOL_OPTIONS=''
        IPADDR=''
        MTU=''
        NAME=''
        NETMASK=''
        NETWORK=''
        REMOTE_IPADDR=''
        STARTMODE='auto'
    - unless: "[ -e /mnt/usr/lib/udev/rules.d/75-persistent-net-generator.rules ]"

# The predictable network interface name can be different depending on
# the kernel / systemd version. One example can be bsc#1168076. To
# avoid this we will create a systemd link.
{{ macros.log('file', 'create_systemd_link_' ~ interface) }}
create_systemd_link_{{ interface }}:
  file.append:
    - name: /mnt/etc/systemd/network/80-{{ interface }}.link
    - text: |
        [Match]
        OriginalName=*
        MACAddress={{ interfaces[interface]['hwaddr'] }}
        [Link]
        Name={{ interface }}
    - unless: "[ -e /mnt/usr/lib/udev/rules.d/75-persistent-net-generator.rules ]"

{{ macros.log('file', 'create_ifcfg_eth' ~ loop.index0) }}
create_ifcfg_eth{{ loop.index0 }}:
  file.append:
    - name: /mnt/etc/sysconfig/network/ifcfg-eth{{ loop.index0 }}
    - text: |
        BOOTPROTO='dhcp'
        BROADCAST=''
        ETHTOOL_OPTIONS=''
        IPADDR=''
        MTU=''
        NAME=''
        NETMASK=''
        NETWORK=''
        REMOTE_IPADDR=''
        STARTMODE='auto'
    - onlyif: "[ -e /mnt/usr/lib/udev/rules.d/75-persistent-net-generator.rules ]"
{% endfor %}

{{ macros.log('file', 'dhcp_hostname') }}
dhcp_hostname:
  file.append:
    - name: /mnt/etc/sysconfig/network/dhcp
    - text:
        - DHCLIENT_SET_HOSTNAME="yes"
        - WRITE_HOSTNAME_TO_HOSTS="no"
