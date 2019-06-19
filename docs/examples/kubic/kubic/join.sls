{% import 'macros.yml' as macros %}

{% set users = pillar['users'] %}
{% set join_params = salt.mine.get(tgt='00:00:00:11:11:11', fun='join_params')['00:00:00:11:11:11'] %}

{{ macros.log('module', 'join_control_plane') }}
join_control_plane:
  module.run:
    - kubeadm.join:
        - api_server_endpoint: {{ join_params['api-server-endpoint'] }}
        - discovery_token_ca_cert_hash: {{ join_params['discovery-token-ca-cert-hash'] }}
        - token: {{ join_params['token'] }}
    - creates: /etc/kubernetes/kubelet.conf

{{ macros.log('loop', 'wait_interfaces_up') }}
wait_interfaces_up:
  loop.until:
    - name: network.interfaces
    - condition: "'flannel.1' in m_ret"
    - period: 5
    - timeout: 300
