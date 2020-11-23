{% import 'macros.yml' as macros %}

{{ macros.log('cmd', 'rpm_exportdb') }}
rpm_exportdb:
  cmd.run:
    - name: rpmdb --root /mnt --exportdb > /mnt/tmp/exportdb
    - creates: /mnt/tmp/exportdb

{{ macros.log('file', 'clean_usr_lib_sysimage_rpm') }}
clean_usr_lib_sysimage_rpm:
  file.absent:
    - name: /mnt/usr/lib/sysimage/rpm

{{ macros.log('cmd', 'rpm_importdb') }}
rpm_importdb:
  cmd.run:
    - name: rpmdb --importdb < /tmp/exportdb
    - root: /mnt
    - onchanges:
      - cmd: rpm_exportdb
