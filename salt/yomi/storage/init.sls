{% set software = pillar['software'] %}

include:
  - .partition
  - .raid
  - .volumes
  - .format
  - .subvolumes
{# TODO: Remove the double check (SumaForm bug) #}
{% if not software.get('image', {}).get('url', '') %}
  - .fstab
  - .mount
{% endif %}