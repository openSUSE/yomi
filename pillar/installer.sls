# Meta pillar for testing Yomi
#
# There are some parameters that can be configured and adapted to
# launch a basic Yomi installation:
#
#   * efi = {True, False}
#   * partition = {'msdos', 'gpt'}
#   * device_type = {'sd', 'hd', 'vd'}
#   * root_filesystem = {'ext{2, 3, 4}', 'btrfs'}
#   * home_filesystem = {'ext{2, 3, 4}', 'xfs', False}
#   * snapper = {True, False}
#   * swap = {True, False}
#   * mode = {'single', 'lvm', 'raid{0, 1, 4, 5, 6, 10}', 'microos',
#             'kubic', 'image', 'sles'}
#
# This meta-pillar can be used as a template for new installers. This
# template is expected to be adapted for production systems, as was
# designed for CI / QA and development.

# We cannot access to grains['efi'] from the pillar, as this is not
# yet synchronized
{% set efi = True %}
{% set partition = 'gpt' %}
{% set device_type = 'sd' %}
{% set root_filesystem = 'btrfs' %}
{% set home_filesystem = 'xfs' %}
{% set snapper = True %}
{% set swap = True %}
{% set mode = 'sles' %}

config:
  events: no
  reboot: yes
{% if snapper and root_filesystem == 'btrfs' %}
  snapper: yes
{% endif %}
  grub2_theme: yes
  grub2_console: {{ 'yes' if efi else 'no' }}
  locale: en_US.UTF-8
  keymap: us
  timezone: UTC
  hostname: node

{% include "_storage.sls.%s" % mode %}

{% if mode == 'sles' %}
suseconnect:
  config:
    regcode: REGISTRATION-CODE
    version: '15.1'
    arch: x86_64
  products:
    - sle-module-basesystem
    - sle-module-server-applications
{% endif %}

software:
  config:
    minimal: {{ 'yes' if mode in ('microos', 'kubic') else 'no' }}
  repositories:
{% if mode == 'sles' %}
    SUSE_SLE-15_GA: "http://download.suse.de/ibs/SUSE:/SLE-15:/GA/standard/"
    SUSE_SLE-15-SP1_GA: "http://download.suse.de/ibs/SUSE:/SLE-15-SP1:/GA/standard/"
{% else %}
    repo-oss: "http://download.opensuse.org/tumbleweed/repo/oss/"
{% endif %}
{% if mode == 'image' %}
  image:
    url: tftp://10.0.3.1/openSUSE-Tumbleweed-Yomi.x86_64-1.0.0.xz
    md5:
{% else %}
  packages:
  {% if mode == 'microos' %}
    - pattern:microos_base
    - pattern:microos_defaults
    - pattern:microos_hardware
    - pattern:microos_apparmor
  {% elif mode == 'kubic' %}
    - pattern:microos_base
    - pattern:microos_defaults
    - pattern:microos_hardware
    - pattern:microos_apparmor
    - pattern:kubic_worker
  {% elif mode == 'sles' %}
    - product:SLES
    - pattern:base
    - pattern:enhanced_base
    - pattern:yast2_basis
    - pattern:x11_yast
    - pattern:x11
    - pattern:gnome_basic
    - kernel-default
  {% else %}
    - pattern:enhanced_base
    - glibc-locale
    - kernel-default
  {% endif %}
{% endif %}

salt-minion:
  configure: yes

services:
  enabled:
{% if mode == 'kubic' %}
    - crio
    - kubelet
{% endif %}
    - salt-minion

users:
  - username: root
    # Set the password as 'linux'. Do not do that in production
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
    # Personal certificate, without the type prefix nor the host
    # suffix
    certificates:
      - "AAAAB3NzaC1yc2EAAAADAQABAAABAQDdP6oez825gnOLVZu70KqJXpqL4fGf\
        aFNk87GSk3xLRjixGtr013+hcN03ZRKU0/2S7J0T/dICc2dhG9xAqa/A31Qac\
        hQeg2RhPxM2SL+wgzx0geDmf6XDhhe8reos5jgzw6Pq59gyWfurlZaMEZAoOY\
        kfNb5OG4vQQN8Z7hldx+DBANPbylApurVz6h5vvRrkPfuRVN5ZxOkI+LeWhpo\
        vX5XK3eTjetAwWEro6AAXpGoQQQDjSOoYHCUmXzcZkmIWEubCZvAI4RZ+XCZs\
        +wTeO2RIRsunqP8J+XW4cZ28RZBc9K4I1BV8C6wBxN328LRQcilzw+Me+Lfre\
        eDPglqx"
