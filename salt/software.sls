{% set filesystems = pillar['filesystems'] %}
{% set software = pillar['software'] %}

{% for device, info in filesystems.items() %}
  {% if info.get('mountpoint') == '/' %}
mount_root_partition_software:
  mount.mounted:
    - name: /mnt
    - device: {{ device }}
    - fstype: {{ info.filesystem }}
    - persist: False

      {% for repo in software.repositories %}
add_repository_{{ repo }}:
  pkgrepo.managed:
    - name: repo-oss
    - baseurl: {{ repo }}
    - refresh: yes
    - gpgautoimport: yes
    - root: /mnt
    - require:
      - mount: mount_root_partition_software
      {% endfor %}

install_packages:
  pkg.installed:
    - pkgs: {{ software.packages }}
    - no_recommends: yes
    - root: /mnt

umount_root_partition_software:
  mount.unmounted:
    - name: /mnt
    - requires: mount_root_partition_software
  {% endif %}
{% endfor %}
