# Use Case: Deployment of Kubic from scratch

We can use [Yomi](https://github.com/openSUSE/yomi) to deploy the
control plane and the workers of a new Kubic cluster.

## Deploying a Kubic control plane node with Yomi

In this section we are going to describe a way to deploy a two-node
Kubic cluster without using `libvirt`. We will require `QEMU`, `socat`
and `dnsmasq`. If you want to use a different mechanism, like using
`libvirt`, `virtualbox` or `vagrant`, you will need to make some
adjustments in the process.

The general process will be to install a local `salt-master`, that
will be used to install MicroOS in two VMs. We will use a salt
orchestrator to provision the operating system and install the
different Kubic components via `kubeadm`. One node of the cluster will
be for the control plane, and the second one will be a worker.

### Installing salt-master and Yomi

We can use the official openSUSE Salt package to control the minions,
but we need in the minions the patched version of Salt. The current
images of JeOS that can be used with Yomi already contains this
patched version for the minion.

```bash
sudo zypper in salt-master salt-standalone-formulas-configuration
```

We can now install the package in our system.

```bash
sudo zypper in yomi-formula
```

### Configuring salt-master

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

### Creating the local network

With QEMU we usually need to create some bridges and tun/tap
interfaces that enable the communication between the local
instances. To provide external access to those instances, we also
usually need to enable the masquerading via `iptables`, and
`ip_forward` via `sysctl` in out host. But using `socat` and `dnsmasq`
we can avoid this.

First, we need to use `socat` to create a new virtual interface named
`vmlan`, that will expose the IP 10.0.3.1 to the host. At the other
side we will have the multicast socket from QEMU.

```bash
sudo socat \
  UDP4-DATAGRAM:230.0.0.1:1234,sourceport=1234,reuseaddr,ip-add-membership=230.0.0.1:127.0.0.1 \
  TUN:10.0.3.1/24,tun-type=tap,iff-no-pi,iff-up,tun-name=vmlan
```

Move this process in a second plane, and check that via `ip a s` we
have the `vmlan` interface.

We will now attach a DHCP / DNS server to this new interface, so the
new nodes will have a predicted IP and hostname. Also the nodes will
find the master using a name that can be resolved.

```bash
sudo dnsmasq --no-daemon \
             --interface=vmlan \
             --except-interface=lo \
             --except-interface=em1 \
             --bind-interfaces \
             --dhcp-range=10.0.3.100,10.0.3.200 \
             --dhcp-option=option:router,10.0.3.101 \
             --dhcp-host=00:00:00:11:11:11,10.0.3.101,cplane \
             --dhcp-host=00:00:00:22:22:22,10.0.3.102,worker \
             --host-record=master,10.0.2.2
```

This command will deliver IPs into the interface `vmlan` from the
range 10.0.3.100 to 10.0.3.200. The service will ignore the petitions
from the local host and the `em1` interface. If your interfaces are
named differently, you will need to adjust the command accordingly.

The hostnames `cplane` and `worker` and `worker2` will be assigned
based on the MAC address, and `cplane` name will be always resolved to
10.0.3.101, the VM that will be assigned to allocate the control plane
services of the cluster.

The `master` record is to be sure that this name resolves to the IP
that QEMU assign to the host node, that is the one that contains the
`salt-master` service.

### Orchestrating the Kubic installation

Now we can launch two nodes. One will be used for the control plane,
and will be assigned with the `cplane` hostname, and the other will be
the single worker.

First we will need to download the Yomi image from
[Factory](https://build.opensuse.org/package/show/openSUSE:Factory/openSUSE-Tumbleweed-Yomi). This
image includes the version of `salt-minion` from openSUSE, that
contains the patches required to execute Yomi.

```bash
osc getbinaries openSUSE:Factory openSUSE-Tumbleweed-Yomi images x86_64
mv binaries/*.iso .
rm -fr binaries
```

In the same directory where our Yomi ISO image is living, we can
launch both nodes. But first, to make the command a bit more compact,
we will copy the OVMF firmware locally.

```bash
cp /usr/share/qemu/ovmf-x86_64-code.bin .
cp /usr/share/qemu/ovmf-x86_64-vars.bin .
```

Now we can launch the nodes:

```bash
NODES=2
for i in $(seq $NODES); do
  # Remove the node fingerprint if needed
  ssh-keygen -R [localhost]:${i}0022 -f ~/.ssh/known_hosts
  # Create the QCOW2 image if needed
  [ -e hda-node${i}.qcow2 ] || qemu-img create -f qcow2 hda-node${i}.qcow2 50G
  cp -af ovmf-x86_64-vars.bin ovmf-x86_64-vars-${i}.bin
  qemu-system-x86_64 -m 2048 -enable-kvm \
    -netdev socket,id=vmlan,mcast=230.0.0.1:1234 \
    -device virtio-net-pci,netdev=vmlan,mac=00:00:00:${i}${i}:${i}${i}:${i}${i} \
    -netdev user,id=net0,hostfwd=tcp::${i}0022-:22 \
    -device virtio-net-pci,netdev=net0,mac=10:00:00:${i}${i}:${i}${i}:${i}${i} \
    -cdrom openSUSE-Tumbleweed*.iso \
    -hda hda-node${i}.qcow2 \
    -drive if=pflash,format=raw,unit=0,readonly,file=./ovmf-x86_64-code.bin \
    -drive if=pflash,format=raw,unit=1,file=./ovmf-x86_64-vars-${i}.bin \
    -smp 2 \
    -boot d &
done
```

You can see if the nodes are answering request with this test:

```bash
salt '*' test.ping
```

If something goes wrong check this in order:

1. `master` can be resolved from the nodes
2. `salt-minion` service is running correctly
3. There is no old key in the master (`salt-key '*' -D`)

For now we need to change a bit the pillar information. `salt-minion`
will be installed in both nodes, and will automatically reconnect to
the master after the first boot. We will need to be sure that the
version of `salt-minion` that is installed is the patched one, so we
will add one extra repository in the pillars.

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
6. Join the worker using `kubeadm` and those secrets
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
