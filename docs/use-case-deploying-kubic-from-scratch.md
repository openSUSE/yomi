# Use Case: Deployment of Kubic from scratch

We can use [Yomi](https://github.com/openSUSE/yomi) to deploy the
control plane and the workers of a new Kubic cluster using SaltStack
to orchestrate the installation.

## Deploying a Kubic control plane node with Yomi

In this section we are going to describe a way to deploy a two-node
Kubic cluster from scratch. One node will be the controller or the
Kubic cluster, and the second node will be the worker.

For this example we can use `libvirt`, `virtualbox`, `vagrant` or
`QEMU`.

We will need to allocate two VMs with:

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

The general process will be to install a local `salt-master`, that
will be used to first install MicroOS in the two VMs. Later we will
use a [Salt
orchestrator](https://docs.saltstack.com/en/latest/topics/orchestrate/orchestrate_runner.html)
to provision the operating system and install the different Kubic
components via `kubeadm`. One node of the cluster will be for the
control plane, and the second one will be a worker.

## Installing salt-master and yomi-formula

We need to install locally the `salt-master` and the `yomi-formula`
packages, as we will control the installation from out laptop or
desktop machine.

```bash
sudo zypper in salt-master salt-standalone-formulas-configuration
sudo zypper in yomi-formula
```

## Configuring salt-master

We are going to use the states from Yomi that are living in
`/usr/share/salt-formulas/yomi`, and some other states are are in
`/usr/share/yomi/kubic`. In order to make both location reachable, we
need to configure `salt-master`.

```bash
sudo cp -a /usr/share/yomi/kubic-file.conf /etc/salt/master.d/
sudo cp -a /usr/share/yomi/pillar.conf /etc/salt/master.d/
```

Optionally, we will configure autosign via UUID, so we can avoid
accept the new `salt-minion` keys during the exercise.

```bash
sudo cp /usr/share/yomi/autosign.conf /etc/salt/master.d/
```

We can now restart the service:

```bash
systemctl restart salt-master.service
```

For a more detailed description read the sections [Looking for the
pillar](../README.md#looking-for-the-pillar) and [Enabling
auto-sign](../README.md#enabling-auto-sign) in the documentation.

## Orchestrating the Kubic installation

Now we can launch two nodes via `libvirt` or `QEMU`. For this last
option read the document [How to use
QEMU](appendix-how-to-use-qemu.md) to take some ideas and make the
proper adjustments on `dnsmasq` to assign correct names for the
different nodes.

You need to boot both nodes with the ISO image or the PXE Boot one,
and check that you can see them locally:

```bash
salt '*' test.ping
```

If something goes wrong check this in order:

1. `master` can be resolved from the nodes
2. `salt-minion` service is running correctly
3. There is no old key in the master (`salt-key '*' -D`)

Adjust the `kubic.sls` from the states to reference properly the
nodes. The provided example is using the MAC address to reference the
nodes:

* `00:00:00:11:11:11`: Control plane node
* `00:00:00:22:22:22`: Worker node

Now we can orchestrate the Kubic installation. So from your host
machine where `salt-master` is running we can fire the orchestrator.

```bash
salt-run state.orchestrate orch.kubic
```

This will execute commands in the `salt-master`, that will:

1. Synchronize all the execution modules, pillars and grains
2. Install MicroOS in both nodes
3. Wait for the reboot of both nodes
4. Install the control plane in `00:00:00:11:11:11`
5. Send a mine to the control plane node, that will collect the
   connection secrets
6. Join the worker (`00:00:00:22:22:22`) using `kubeadm` and those
   secrets
7. Remove the mine

This orchestrator is only an example, and there are elements that can
be improved. The main one is that inside the YAML file there are
references to the minion ID of the control plane and the worker,
something that is better to put in the pillar.

Another problem is that in the current version of Salt, we cannot send
asynchronous commands to the orchestrator. This imply that there is a
race condition in the section that wait for the node reboot. If one
node reboot before than the other, there is a chance that the reboot
event will be lost before the `salt.wait_for_event` is reached. The
next version of Salt, Neon, will add this capability, and the example
will be updated accordingly.

If this race condition happens, you can wait manually to the reboot,
comment the `salt.wait_for_event` entry in `kubic.sls`, and relaunch
the `salt-run` command.
