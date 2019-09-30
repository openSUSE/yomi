synchronize_all:
  salt.function:
    - name: saltutil.sync_all
    - tgt: '*'

install_microos:
  salt.state:
    - sls:
      - yomi
    - tgt: '*'

wait_for_reboots:
  salt.wait_for_event:
    - name: salt/minion/*/start
    - id_list:
      - '00:00:00:11:11:11'
      - '00:00:00:22:22:22'
    - require:
      - salt: install_microos

install_control_plane:
  salt.state:
    - tgt: '00:00:00:11:11:11'
    - sls:
      - kubic.control_plane

send_mine:
  salt.function:
    - name: mine.send
    - tgt: '00:00:00:11:11:11'
    - arg:
      - join_params
    - kwarg:
        mine_function: kubeadm.join_params
        create_if_needed: yes

join_worker:
  salt.state:
    - tgt: '00:00:00:22:22:22'
    - sls:
      - kubic.join

delete_mine:
  salt.function:
    - name: mine.delete
    - tgt: '*'
    - arg:
      - join_params
