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
#   * network = {'auto', 'eth0', 'ens3', ... }
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
{% set home_filesystem = False %}
{% set snapper = True %}
{% set swap = False %}
{% set mode = 'microos' %}
{% set network = 'auto' %}

{% set arch = grains['cpuarch'] %}

config:
  events: no
  reboot: no
{% if snapper and root_filesystem == 'btrfs' %}
  snapper: yes
{% endif %}
  locale: en_US.UTF-8
  keymap: us
  timezone: UTC
  hostname: node

{% include "_storage.sls.%s" % mode %}

{% if mode == 'sles' %}
suseconnect:
  config:
    regcode: INTERNAL-USE-ONLY-f7fe-e9d9
    version: '15.2'
    arch: {{ arch }}
  products:
    - sle-module-basesystem
    - sle-module-server-applications
{% endif %}

software:
  config:
    minimal: {{ 'yes' if mode in ('microos', 'kubic') else 'no' }}
    enabled: yes
    autorefresh: yes
    gpgcheck: yes
  repositories:
{% if mode == 'sles' %}
    SUSE_SLE-15_GA: "http://download.suse.de/ibs/SUSE:/SLE-15:/GA/standard/"
    SUSE_SLE-15_Update: "http://download.suse.de/ibs/SUSE:/SLE-15:/Update/standard/"
    SUSE_SLE-15-SP1_GA: "http://download.suse.de/ibs/SUSE:/SLE-15-SP1:/GA/standard/"
    SUSE_SLE-15-SP1_Update: "http://download.suse.de/ibs/SUSE:/SLE-15-SP1:/Update/standard/"
    SUSE_SLE-15-SP2_GA: "http://download.suse.de/ibs/SUSE:/SLE-15-SP2:/GA/standard/"
    SUSE_SLE-15-SP2_Update: "http://download.suse.de/ibs/SUSE:/SLE-15-SP2:/Update/standard/"
{% elif arch == 'aarch64' %}
    repo-oss: "http://download.opensuse.org/ports/aarch64/tumbleweed/repo/oss/"
{% else %}
    repo-oss:
      url: "http://download.opensuse.org/tumbleweed/repo/oss/"
      name: openSUSE-Tumbleweed
{% endif %}
{% if mode == 'image' %}
  image:
    url: tftp://10.0.3.1/openSUSE-Tumbleweed-Yomi{{ arch }}-1.0.0.xz
    md5:
{% else %}
  packages:
  {% if mode == 'microos' %}
    - pattern:microos_base
    - pattern:microos_defaults
    - pattern:microos_hardware
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
  {% else %}
    - pattern:enhanced_base
    - glibc-locale
  {% endif %}
    - kernel-default
{% endif %}

salt-minion:
  config: yes

services:
  enabled:
{% if mode == 'kubic' %}
    - crio
    - kubelet
{% endif %}
    - salt-minion

{% if network != 'auto' %}
networks:
  - interface: {{ network }}
{% endif %}

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
