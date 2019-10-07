{% import 'macros.yml' as macros %}

{% for fstype, fs_file in (('devtmpfs', '/mnt/dev'), ('proc', '/mnt/proc'), ('sysfs', '/mnt/sys')) %}
{{ macros.log('mount', 'mount_' ~ fs_file) }}
mount_{{ fs_file }}:
  mount.mounted:
    - name: {{ fs_file }}
    - device: {{ fstype }}
    - fstype: {{ fstype }}
    - mkmnt: yes
    - persist: no
{% endfor %}
