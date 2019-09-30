{% set software = pillar['software'] %}

include:
  - .partition
  - .raid
  - .volumes
  - .format
  - .subvolumes
{% if software.get('image', {}) %}
  - .fstab
  - .mount
{% endif %}