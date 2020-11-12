{% import 'macros.yml' as macros %}

{% set networks = pillar.get('networks') %}

{% if networks %}
  {% for network in networks %}
create_ifcfg_{{ network.interface }}:
  file.append:
    - name: /mnt/etc/sysconfig/network/ifcfg-{{ network.interface }}
    - text: |
        NAME=''
        BOOTPROTO='dhcp'
        STARTMODE='auto'
        ZONE=''
  {% endfor %}
{% else %}
# This assume that the image used for deployment is under a
# predictable network interface name, like Tumbleweed. For SLE, boot
# the image with `net.ifnames=1`

  {% set interfaces = salt.network.interfaces() %}
  {% set interfaces_except_lo = interfaces | select('!=', 'lo') %}

  {% for interface in interfaces_except_lo %}
{{ macros.log('file', 'create_ifcfg_' ~ interface) }}
create_ifcfg_{{ interface }}:
  file.append:
    - name: /mnt/etc/sysconfig/network/ifcfg-{{ interface }}
    - text: |
        NAME=''
        BOOTPROTO='dhcp'
        STARTMODE='auto'
        ZONE=''
    - unless: "[ -e /mnt/usr/lib/udev/rules.d/75-persistent-net-generator.rules ]"

{{ macros.log('file', 'create_ifcfg_eth' ~ loop.index0) }}
create_ifcfg_eth{{ loop.index0 }}:
  file.append:
    - name: /mnt/etc/sysconfig/network/ifcfg-eth{{ loop.index0 }}
    - text: |
        NAME=''
        BOOTPROTO='dhcp'
        STARTMODE='auto'
        ZONE=''
    - onlyif: "[ -e /mnt/usr/lib/udev/rules.d/75-persistent-net-generator.rules ]"

{{ macros.log('cmd', 'write_net_rules_eth' ~ loop.index0) }}
write_net_rules_eth{{ loop.index0 }}:
  cmd.run:
    - name: /usr/lib/udev/write_net_rules
    - env:
        - INTERFACE: eth{{ loop.index0 }}
        - MATCHADDR: "{{ interfaces[interface].hwaddr }}"
    - root: /mnt
    - onlyif: "[ -e /mnt/usr/lib/udev/rules.d/75-persistent-net-generator.rules ]"
  {% endfor %}
{% endif %}

{{ macros.log('file', 'dhcp_hostname') }}
dhcp_hostname:
  file.append:
    - name: /mnt/etc/sysconfig/network/dhcp
    - text:
        - DHCLIENT_SET_HOSTNAME="yes"
        - WRITE_HOSTNAME_TO_HOSTS="no"
