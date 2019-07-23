# Appendix: Notes about the Yomi live image

Yomi is a set of Salt states that are used to drive the installation
of a new operating system. To take full control of the system where
the installation will be done, you will need to boot from an external
system that provides an already configured `salt-minion`, and a set of
CLI tools required during the installation.

We can deploy all the requirements using different mechanism. One, for
example, is via PXE boot. We can build a server that will deliver the
Linux `kernel` and an `initrd` will all the required software. Another
alternative is to have an already live ISO image that you use to boot
from the USB port.

There is an already available image that contains all the requirements
in
[OBS](https://build.opensuse.org/package/show/home:aplanas:Images/openSUSE-Tumbleweed-JeOS). This
is an JeOS based image build from openSUSE Tumbleweed
repositories. Also contains a version of `salt-minion` with all the
code that is under review in the SaltStack project, that is required
to run all the states required by Yomi.

The image is configured to simplify the discovery and integration of
systems booted from it. For example, the image is configured to take
advantage of the auto-sign feature of SaltStack, among others details
like indicating the master ID from the boot command line.

## Autosign via UUID

The Yomi image that contains `salt-minion` have already some grains
that publish some UUIDs from a restricted list. We can use this
information from the `salt-master` to recognize nodes that are ready
to be installed, and avoid the acceptance of the key in the master.

During the creation of the image in OBS, a random UUID using a DNS
name-space is generated and assigned to the `salt-minion` service that
will be executed after the boot process.

The `salt-master` in your network needs to be configured to recognize
and accept those UUIDs. If we have the `yomi-formula` package
installed, we can enable this feature copying the configuration
snipped that comes in the package and restarting the server:

```bash
cp /usr/share/yomi/autosign.conf /etc/salt/master.d/
systemctl restart salt-master.service
```

If we want to enable this service manually, we will first to generate
the list of valid UUIDs:

```bash
mkdir -p /etc/salt/autosign_grains/
for i in $(seq 0 9); do
    echo $(uuidgen --md5 --namespace @dns --name http://opensuse.org/$i)
done > /etc/salt/autosign_grains/uuid
```

Now we need to enable this option in master configuration, and restart
the service:

```bash
echo "autosign_grains_dir: /etc/salt/autosign_grains" > /etc/salt/master.d/autosign.conf
systemctl restart salt-master.service
```

With this feature enabled we can skip the `salt-key -A` for nodes
booted from the Yomi image.

## Finding the master node

The `salt-minion` configuration in the Yomi image will search the
`salt-master` system under the `master` name. Is expected that the
local DNS service will resolve the `master` name to the correct IP
address.

During boot time of the Yomi image we can change the address where is
expected to find the master node. To do that we can enter under the
GRUB menu the entry `master=my_master_address`.

An internal systemd service in the image will detect this address and
configure the `salt-minion` accordingly.

Under the current Yomi states, this address will be copied under the
new installed system, together with the key delivered by the
`salt-master` service. This means that once the system is fully
installed with the new operating system, the new `salt-minion` will
find the master directly after the first boot.

## Setting the minion ID

In a similar way, during the boot process we can set the minion ID
that will be assigned to the `salt-minion`. Using the parameter
`minion_id`. For example, `minion_id=worker01` will set the minion ID
for this system as 'worker01'.

The small service that read the boot command line, will use by default
the host name as the minion ID if no parameter is set. This will make
very easy to set the ID via DHCP. But if there is not host name (other
than localhost), the MAC address of the first interface will be used.
