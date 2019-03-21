# Yomi - Yet one more installer

# What is Yomi

Yomi (yet one more installer) is a new proposal for an installer for
the [open]SUSE family. It is designed as a
[SaltStack](https://www.saltstack.com/) state, and expected to be used
in situations were unattended installations for heterogeneous nodes is
required, and where some bits of intelligence in the configuration file,
can help to customize the installation.

Being also a Salt state makes the installation process one more step
during the provisioning stage, making on Yomi a good candidate for
integration in any workflow were SaltStack is used.


# Installation

To execute Yomi we need a modern version of Salt, as we need special
features are only on the
[develop](https://github.com/saltstack/salt/tree/develop) branch of
Salt. Technically we can use the last released version of Salt for
salt-master, but for the minions we need the most up-to-date version.

For openSUSE Tumbleweed I create a [package of
Salt](https://build.opensuse.org/package/show/home:aplanas:branches:systemsmanagement:saltstack:testing/salt)
that contains the last released version and a patch with the missing
code that only lives on the develop branch of the code. This is the
package required to be installed where the salt-minion is executed.

To simplify the test and development of Yomi, I also provide a JeOS
(Tumbleweed) based
[image](https://build.opensuse.org/package/show/home:aplanas:Images/test-image-iso)
that includes this patched package. You can use this ISO to boot the node.

## Installing salt-master

You can read the [official
documentation](https://docs.saltstack.com/en/latest/topics/installation/index.html)
about how to install salt-master. For this documentation we are going
to show only the one based on Python virtual environments.

```Bash
python3 -mvenv venv

source venv/bin/activate

pip install --upgrade pip
pip install salt
```

Once the Salt code is living in the venv, we can configure it.

```Bash
mkdir -p venv/etc/salt/pki/{master,minion} \
      venv/etc/salt/autosign_grains \
      venv/var/cache/salt/master/file_lists/roots

cat <<EOF > venv/etc/salt/master
root_dir: $(pwd)/venv

file_roots:
  base:
    - $(pwd)/srv/salt

pillar_roots:
  base:
    - $(pwd)/srv/pillar
EOF
```

To find more configuration options for salt-master, refer always to
the official documentation. Here we set a very minimal one, we only
specify where to find the salt states, the pillars and from where we
consider the root directory.

## Enabling Autosign

To simplify the discovery and key management of the minions, we can
use the auto-sign feature of Salt. To do that we need to add a new
line into the master configuration file.

```Bash
echo "autosign_grains_dir: /etc/salt/autosign_grains" >> venv/etc/salt/master
```

The ISO image that I prepared already export some UUIDs generated for
each minion, so we need to list into the master all the possible valid
UUIDs.

```Bash
mkdir -p venv/etc/salt/autosign_grains

for i in $(seq 0 9); do
  echo $(uuidgen --md5 --namespace @dns --name http://opensuse.org/$i)
done > venv/etc/salt/autosign_grains/uuid
```

We can start now the salt-master service manually:

```Bash
salt-master -c venv/etc/salt &
```

## Salt API

Yomi includes a monitoring tool, that read from the event bus of
Salt. To enable the real-time events we need to enable set `events`
field to `yes` in the configuration section of the pillar. This
`monitor` tool will connect to the salt-api service to read the status
and send request to Salt, all done via the REST protocol.

We will use CherryPy to serve the requests of Salt API, and we will
also install a basic WebSocket Python library. Supposing that the
virtual environment is activated, we can:

```Bash
pip install cherrypy ws4py
```

As configuration example, we will setup Salt API to use CherryPy,
listen on port 8000, disable SSL and use an eauth based of a plain
text file. Of course this setup is only for testing.

```Bash
mkdir -p venv/etc/salt/master.d

cat <<EOF > venv/etc/salt/master.d/salt-api.conf
rest_cherrypy:
  port: 8000
  debug: no
  disable_ssl: yes
EOF

cat <<EOF > venv/etc/salt/master.d/eauth.conf
external_auth: 
  file:
    ^filename: $(pwd)/venv/etc/user-list.txt
    salt:
      - .*
      - '@wheel'
      - '@runner'
      - '@jobs'
EOF

echo "salt:linux" > venv/etc/user-list.txt
```

The last line add the user `salt` (with password `linux`) to the user
list file.

After launching salt-master, we can start the Salt API service:

```Bash
salt-api -c venv/etc/salt &
```

With this configuration in place, the monitoring can be done with this
configuration:

```Bash
export SALTAPI_URL=http://localhost:8000
export SALTAPI_EAUTH=file
export SALTAPI_USER=salt
export SALTAPI_PASS=linux

monitor -r -y
```

The `monitor` tool store in a local cache the authentication tokens
generated by Salt API. This will accelerate the next connection to the
service, but sometimes can cause authentication errors (for example,
when the cache is in place but the salt-master get reinstalled). The
option `-r` makes sure that this cache is removed before
connection. Check the help option of the tool for more information.


# Pillars in Yomi

To install a new node, we need to provide some data to describe the
installation requirements, like the layout of the partitions, file
systems used, or what software to install inside the new
deployment. This data is collected in what is Salt is known as a
[pillar](https://docs.saltstack.com/en/latest/topics/tutorials/pillar.html).

Pillars can be associated with certain nodes in our network, making of
this technique a basic one to map a description of how and what to
install into a node. This mapping is done via the `top.sls` file:

```YAML
base:
  'C7:7E:55:62:83:17':
    - controller
```

In `controller.sls` we will describe in detail the installation
parameters that will be applied to the node which minion-id match with
`C7:7E:55:62:83:17`. Note that in this example we are using the MAC
address of the first interface as a minion-id (check the section
**Enabling Autosign** for an example).

The `controller.sls` pillar consist on several sections, that we can
describe here.

## `config` section

The `config` section contains global configuration options that will
affect the installer.

* `events`: Boolean. Optional. Default: `yes`

  Yomi can fire Salt events before and after the execution of the
  internal states that Yomi use to drive the installation. Using the
  Salt API, WebSockets, or any other mechanism provided by Salt, we
  can listen the event bus and use this information to monitor the
  installer. Yomi provides a basic tool, `monitor`, that shows real
  time information about the installation process.

  To disable the events, set this parameter to `no`.

  Note that this option will add three new states for each single Yomi
  state. One extra state is executed always before the normal state,
  and is used to signalize that a new state will be executed. If the
  state is successfully terminated, a second extra state will send an
  event to signalize that the status of the state is positive. But if
  the state fails, a third state will send the fail signal. All those
  extra states will be showed in the final report of Salt.

* `kexec`: Boolean. Optional. Default: `yes`

  Instead of rebooting, reload the new kernel installed in the
  node. If the value is `no` there will be no reboot. This behavior is
  planned to change.

* `snapper`: Boolean. Optional. Default: `no`

  In Btrfs configurations (and in LVM, but still not implemented) we
  can install the snapper tool, to do automatic snapshots before and
  after updates in the system. One installed, a first snapshot will be
  done and the GRUB entry to boot from snapshots will be added.

* `grub2_theme`: Boolean. Optional. Default: `no`

  If `yes` the `grub2-branding-openSUSE` package will be installed and
  configured.

* `grub2_console`: Boolean. Optional. Default: `no`

  If `yes` Yomi will append `console=tty0 console=ttyS0,115200` in the
  Linux command line during the boot. This option is help full when
  the we want to have serial access to console to the new machine.

Example:

```YAML
config:
  # Do not send events, useful for debugging
  events: no
  # Do not reboot after installation
  kexec: no
  # Always install snapper if possible
  snapper: yes
```

## `partitions` section

Yomi separate partitioning the devices from providing a file system,
creating volumes or building arrays of disks. The advantage of this is
that this, usually, compose better that other approaches, and makes
more easy adding more options that needs to work correctly with the
rest of the system.

* `config`: Dictionary. Optional.

  Subsection that store some configuration options related with the
  partitioner.

  * `label`: String. Optional. Default: `msdos`

    Default label for the partitions of the devices. We use any
    `parted` partition recognized by `mklabel`, like `gpt`, `msdos` or
    `bsd`. For UEFI systems, we need to set it to `gpt`.

  * `alignment`: Integer. Optional. Default: `1`

    Gap, in MB, leave before the first partition. Usually is 1MB, so
    GRUB have room to write the code needed after the MBR, and the
    sectors are aligned for multiple SSD and hard disk devices.

* `devices`: Dictionary.

  List of devices that will be partitioned. We can indicate already
  present devices, like `/dev/sda` or `/dev/hda`, but we can also
  indicate devices that will be present after the RAID configuration,
  like `/dev/md0` or `/dev/md/myraid`. We can use any valid device
  name in Linux such as all the `/dev/disk/by-id/...`,
  `/dev/disk/by-label/...`, `/dev/disk/by-uuid/...` and others.

  For each device we have:

  * `label`: String. Optional. Default: `msdos`

    Partition label for the device. The meaning and the possible
    values are identical for `label` in the `config` section.

  * `partitions`: Array. Optional.

    Partitions inside a device are described with an array. Each
    element of the array is a dictionary that describe a single
    partition.

    * `number`: Integer. Optional. Default: `loop.index`

      Expected partition number. Eventually this parameter will be
      really optional, when the partitioner can deduce it from other
      parameters. Today is better to be explicit in the partition
      number, as this will guarantee that the partition is found in
      the hard disk if present.

    * `size`: Float.

      Size of the partition expressed in MB. In future versions this
      will change, and will be expressed in different absolute and
      relative units.

    * `type`: String.

      A string that indicate for what this partition will be
      used. Yomi recognize several types:

      * `swap`: This partition will be used for SWAP.
	  * `linux`: Partition used to root, home or any data.
	  * `boot`: Small partition used for GRUB when in BIOS and `gpt`.
	  * `efi`: EFI partition used by GRUB when UEFI.
	  * `lvm`: Partition used to build an LVM physical volume.
	  * `raid`: Partition that will be a component of an array.

Example:

```YAML
partitions:
  config:
    label: gpt
  devices:
    /dev/sda:
      partitions:
        - number: 1
          size: 512
          type: efi
        - number: 2
          size: 2048
          type: swap
        - number: 3
          size: 20480
          type: linux
```

## `lvm` section

To build an LVM we usually create some partitions (in the `partitions`
section) with the `lvm` type set, and in the `lvm` section we describe
the details. This section is a dictionary, were each key is the name
of the LVM volume, and inside it we can find:

* `vgs`: Array.

  List of components (partitions or full devices) that will constitute
  the physical volumes and the virtual group of the LVM. Note that the
  name of the virtual group will be the key where this definition is
  under.

* `lvs`: Array.

  Each element of the array will define:

  * `name`: String.

    Name of the logical volume under the volume group.

  * `size`: String.

    Size of the logical volume, but can include a prefix to indicate
    units. Those units are equivalent to the ones that lvcreate can
    understand.

Example:

```YAML
lvm:
  system:
    vgs:
      - /dev/sda1
      - /dev/sdb1
      - /dev/sdc1
    lvs:
      - name: swap
        size: 2048M
      - name: root
        size: 10240M
      - name: home
        size: 20480M
```

## `raid` section

In the same way that LVM, to create RAID arrays we can setup first
partitions (with the type `raid`) and configure the details in this
section. Also, similar to the LVM section, the keys a correspond to
the name of the device where the RAID will be created. Valid values
are like `/dev/md0` or `/dev/md/system`.

* `level`: String.

   RAID level. Valid values can be `linear`, `raid0`, `0`, `stripe`,
   `raid1`, `1`, `mirror`, `raid4`, `4`, `raid5`, `5`, `raid6`, `6`,
   `raid10`, `10`, `multipath`, `mp`, `faulty`, `container`.

* `devices`: Array.

  List of devices or partitions that build the array.

* `metadata`: String. Optional. Default: `default`

  Metadata version for the superblock. Valid values are `0`, `0.9`,
  `1`, `1.0`, `1.1`, `1.2`, `default`, `ddm`, `imsm`.

The user can specify more parameters that will be passed directly to
`mdadm`, like `spare-devices` to indicate the number of extra devices
in the initial array, or `chunk` to speficy the chunk size.

Example:

```YAML
raid:
  /dev/md0:
    level: 1
    devices:
      - /dev/sda1
      - /dev/sdb1
      - /dev/sdc1
    spare-devices: 1
    metadata: 1.0
```

## `filesystems` section

The partitions, devices or arrays created in previous sections usually
requires a file system. This section will simply list the device name
and the file system (and properties) that will be applied to it.

* `filesystem`. String.

  File system to apply in the device. Valid values are `swap`,
  `linux-swap`, `bfs`, `btrfs`, `cramfs`, `ext2`, `ext3`, `ext4`,
  `minix`, `msdos`, `vfat`. Technically Salt will search for a command
  that match `mkfs.<filesystem>`, so the valid options can be more
  extensive that the one listed here.

* `mountpoint`. String.

  Mount point where the device will be registered in `fstab`.

* `fat`. Integer. Optional.

  If the file system is `vfat` we can force the FAT size, like 12, 16
  or 32.

* `subvolumes`. Dictionary.

  For `btrfs` file systems we can specify more details.

  * `prefix`. String. Optional.

    `btrfs` sub-volume name where the rest of the sub-volumes will be
    under. For example, if we set `prefix` as `@` and we create a
    sub-volume named `var`, Yomi will create it as `@/var`.

  * `subvolume`. Dictionary.

    * `path`. String.

      Path name for the sub-volume.

	* `copy_on_write`. Boolean. Optional. Default: `yes`

      Value for the copy-on-write option in `btrfs`.

Example:

```YAML
filesystems:
  /dev/sda1:
    filesystem: vfat
    mountpoint: /boot/efi
    fat: 32
  /dev/sda2:
    filesystem: swap
  /dev/sda3:
    filesystem: btrfs
    mountpoint: /
    subvolumes:
      prefix: '@'
      subvolume:
        - path: home
        - path: opt
        - path: root
        - path: srv
        - path: tmp
        - path: usr/local
        - path: var
          copy_on_write: no
        - path: boot/grub2/i386-pc
        - path: boot/grub2/x86_64-efi
```

## `bootloader` section

* `device`: String.

  Device name where GRUB2 will be installed. Yomi will take care of
  detecting if is a BIOS or an UEFI setup, and also if Secure-Boot in
  activated, to install and configure the bootloader (or the shim
  loader)

Example:

```YAML
bootloader:
  device: /dev/sda1
```

## `software` section

We can indicate the repositories that will be registered in the new
installation, and the packages and patterns that will be installed.

* `repositories`. Dictionary.

  Each key of the dictionary will be the name under where this
  repository is registered, and the key is the URI associated with it.

* `packages`. Array.

  List of packages or patters to be installed.

Example:

```YAML
software:
  repositories:
    repo-oss: "http://download.opensuse.org/tumbleweed/repo/oss"
  packages:
    - patterns-base-base
    - kernel-default
```

## `users` section

In this section we can list a simple list of users and passwords that
we expect to find once the system is booted.

* `username`. String.

  Login or username for the user.

* `password`. String.

  Shadow password hash for the user.

Example:

```YAML
users:
  - username: root
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
  - username: aplanas
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
```


# How Yomi works.

TBD
