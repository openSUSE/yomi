{% import 'macros.yml' as macros %}

{% for fs_file in ('/mnt/sys', '/mnt/proc', '/mnt/dev' ) %}
{{ macros.log('mount', 'umount_' ~ fs_file) }}
umount_{{ fs_file }}:
  mount.unmounted:
    - name: {{ fs_file }}
    - requires: mount_{{ fs_file }}
{% endfor %}
