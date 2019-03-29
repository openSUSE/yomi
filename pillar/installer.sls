# Meta pillar for testing Yomi
#
# There are some parameters that can be configured and adapted to
# launch a basic Yomi installation:
#
#   * efi = {True, False}
#   * partition = {'msdos', 'gpt'}
#   * root_filesystem = {'ext{2, 3, 4}', 'btrfs'}
#   * home_filesystem = {'ext{2, 3, 4}', 'xfs', False}
#   * snapper = {True, False}
#   * swap = {True, False}
#   * mode = {'single', 'lvm', 'raid{0, 1, 4, 5, 6, 10}'}
#
# This meta-pillar can be used as a template for new installers.

# We cannot access to grains['efi'] from the pillar, as this is not
# yet synchronized
{% set efi = True %}
{% set partition = 'msdos' %}
{% set root_filesystem = 'ext4' %}
{% set home_filesystem = False %}
{% set snapper = False %}
{% set swap = False %}
{% set mode = 'single' %}

config:
  events: yes
  kexec: yes
{% if snapper and root_filesystem == 'btrfs' %}
  snapper: yes
{% endif %}
  grub2_theme: yes
{% if efi %}
  grub2_console: yes
{% endif %}

{% include "_storage.sls.%s" % mode %}

software:
  repositories:
    repo-oss: "http://download.opensuse.org/tumbleweed/repo/oss"
  packages:
    - patterns-base-base
    - kernel-default

users:
  - username: root
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
  - username: aplanas
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
