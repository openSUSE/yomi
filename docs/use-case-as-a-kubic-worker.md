# Use Case: A Kubic worker provisioned with Yomi

We can use [Yomi](https://github.com/openSUSE/yomi) to deploy worker
nodes in an already deployed Kubic cluster.

## Overview and requirements

In this section we are going to describe a way to deploy a two-node
Kubic cluster, and use Yomi to provision a third node.

For this example we can use `libvirt`, `virtualbox`, `vagrant` or
`QEMU`.

We will need to allocate three VMs with:

* 50GB of hard disk
* 2 CPU per node
* 2048MB RAM per system

We will need also connectivity bewteen the different VMs to form a
local network, and also access to Internet for downloading packages.

You can check
[appendix-how-to-use-qemu.md](appendix-how-to-use-qemu.md) to learn
about how to do this with QEMU and how to setup a DNS server with
`dnsmasq` to create a network configuration that will meet the
requirements.

## Installing MicroOS for Kubic

Follow the documentation about how to install a two node Kubic cluster
from the [Kubic
documentation](https://en.opensuse.org/Kubic:kubeadm). In a nutshell
the process is:

* Spin two empty nodes with QEMU / libvirt
* Boot both nodes using the [Kubic
  image](http://download.opensuse.org/tumbleweed/iso/openSUSE-Kubic-DVD-x86_64-Current.iso)
* Deploy one node with the 'Kubic Admin Node' role, this will install
  CRI-O, `kubeadn` and `kubicctl`, together with `salt-master`.
* Deploy the second node with the system role 'Kubic Worker Node'.

We will use `kubicctl` to deploy Kubernetes in the control plane, and
use this same tool to join the already installed worker.

If the control plane node have more that one interface (for example,
if we use QEMU as described in the appendix documentation this will be
the case, but not if we use libvirt), we need to identify the one that
is visible from the worker node. We will pass the IP of this interface
via the `--adv-addr` parameter.

```bash
kubicctl init --adv-addr 10.0.3.101
```

If there are not multiple interfaces and we want to use `flannel` as a
pod network, as simple `kubicctl init` will work on most of the cases.

In the worker node we need to set up `salt-minion` so in can connect
to the `salt-master` in the control plane node. We need to find the
address or IP address that can be used to point to the master,
configure the minion and restart the service.

```bash
echo "master: <MASTER-IP>" > /etc/salt/minion.d/master.conf
systemctl enable --now salt-minion.service
```

The minion now try to connect to the master, but before this can
succeed we need to accept the key in the `master` node.

```bash
salt-key -A
```

We can test from the master that the minion is answering properly:

```bash
salt worker1 test.ping
```

Now we can join the node from the `master` one:

```bash
kubicctl node add worker1
```

Note that `worker1` is refers here to the minion ID that Salt
recognize, not the host name of the worker node.

If the command succeed, we inspect the cluster status:

```bash
kubectl get nodes
```

It will show something like:

```
NAME      STATUS   ROLES    AGE   VERSION
master    Ready    master   11m   v1.15.0
worker1   Ready    <none>   56s   v1.15.0
```

If `kubectl` fails, check that `/etc/kubernetes/admin.conf` is copied
as `~/.kube/config` as documented in `kubeadm`.

## Provisioning a Kubic worker with Yomi

The first worker was allocated via the Kubic DVD image. This is
reasonable for small clusters, but we can simplify the work if we can
install MicroOS on new nodes using SaltStack and later join the node
to the cluster with `kubicctl`.

### Yomi image and Yomi package

Yomi is a set of Salt states that will allows the provisioning of
systems. We will need to boot the new node using a JeOS image that
contains a `salt-minion` service, that later can be controlled from
the `master` node, that is where `salt-master` is installed.

You can find mode information about this Yomi image in the [Booting a
new machine](../README.md#booting-a-new-machine) section if the main
documentation.

Download the ISO image or the PXE Boot one (check the previous link
the learn how to configure the PXE Boot one). Optionally configure the
`salt-master` to enable the auto-sign feature via UUID, as described
in the [Enabling auto-sign](../README.md#enabling-auto-sign) section.

In the `master` node we will need to install the `yomi-formula`
package from Factory.

```bash
transactional-update pkg install yomi-formula
reboot
```

We can now boot a new node in the same network that the Kubic cluster,
using the Yomi image. Be sure (via boot parameter or later
configuration) that the `salt-minion` can find the already present
master, and if needed accept the key.

### Adding the new worker

We need to set the pillar data that Yomi will use to make a new
installation. This data will describe installation details like how
will be the hard disk partition layout, the different packages that
will be installed or the services that will be enabled before booting.

The packages `yomi-formula` already provides and example for a MicroOS
installation, so we can use it as a template.

Read the section [Configuring the
pillar](../README.md#configuring-the-pillar) to learn more about the
pillar examples provided by the package, and how to copy them in a
place that we can edit them.

The `yomi-formula` package do not include an example `top.sls`, but we
can create one easily for this example.

```bash
cat <<EOF > /srv/salt/top.sls
base:
  '*':
    - yomi
EOF
```

Check also that for the pillar we also have a `top.sls`. The one that
we have in the package as an example is:

```yaml
base:
  '*':
    - installer
```

Now we can [get information about the
hardware](../README.md#getting-hardware-information) available in the
new worker node, and adjust the pillar accordingly.

Optionally we can [wipe the disks](../README.md#cleaning-the-disks),
and then apply the `yomi` state.

```bash
salt worker2 state.apply
```

Once the node is back, we can proceed as usual:

```bash
kubicctl node add worker2
```
