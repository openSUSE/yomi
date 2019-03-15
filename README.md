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

TBD

##


## Enabling Autosign

TBD


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

* : Integer. Optional. Default: 0

  Number if extra devices in the initial array.

The user can specify more parameters, that will be passed directly to
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

Example:

```YAML
filesystems:
  /dev/sda1:
    filesystem: vfat
    mountpoint: /boot/efi
    # fat: 32
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

Example:

```YAML
bootloader:
  device: /dev/sda1
```

## `software` section

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

Example:

```YAML
users:
  - username: root
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
  - username: aplanas
    password: "$1$wYJUgpM5$RXMMeASDc035eX.NbYWFl0"
```
