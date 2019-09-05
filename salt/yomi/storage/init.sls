{% set software = pillar['software'] %}

include:
  - .partition
  - .raid
  - .volumes
  - .format
  - .subvolumes
{% if 'image' not in software %}
  - .fstab
  - .mount
{% endif %}