# TODO(aplanas): Think about a better guard
{% if not salt.file.file_exists('/etc/yomi-installed') %}
include:
  - .storage
  - .software
  - .users
  - .bootloader
  - .services
  - .post_install
  - .reboot
{% endif %}
