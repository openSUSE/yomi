{% import 'macros.yml' as macros %}

{% set users = pillar['users'] %}
{% set public_ip = grains['ip4_interfaces']['ens4'][0] %}

{{ macros.log('module', 'install_kubic') }}
install_kubic:
  module.run:
    - kubeadm.init:
        - apiserver_advertise_address: {{ public_ip }}
        - pod_network_cidr: '10.244.0.0/16'
    - creates: /etc/kubernetes/admin.conf

{% for user in users %}
  {% set username = user.username %}
{{ macros.log('file', 'create_kubic_directory_' ~ username) }}
create_kubic_directory_{{ username }}:
  file.directory:
    - name: ~{{ username }}/.kube
    - user: {{ username }}
    - group: {{ username if username == 'root' else 'users' }}
    - mode: 700

{{ macros.log('file', 'copy_kubic_configuration_' ~ username) }}
copy_kubic_configuration_{{ username }}:
  file.copy:
    - name: ~{{ username }}/.kube/config
    - source: /etc/kubernetes/admin.conf
    - user: {{ username }}
    - group: {{ username if username == 'root' else 'users' }}
    - mode: 700
{% endfor %}

{{ macros.log('cmd', 'install_network') }}
install_network:
  cmd.run:
    - name: kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/bc79dd1505b0c8681ece4de4c0d86c5cd2643275/Documentation/kube-flannel.yml
    - unless: ip link | grep -q flannel

{{ macros.log('loop', 'wait_interfaces_up') }}
wait_interfaces_up:
  loop.until:
    - name: network.interfaces
    - condition: "'flannel.1' in m_ret"
    - period: 5
    - timeout: 300
