# Use Case: A Kubic worker provisioned with Yomi

We can use [Yomi](https://github.com/openSUSE/yomi) to deploy worker
nodes in an already deployed Kubic cluster.

## Deploying a Kubic cluster with QEMU

In this section we are going to describe a way to deploy a two-node
Kubic cluster without using `libvirt`. We will require `QEMU`, `socat`
and `dnsmasq`. If you already have a real Kubic cluster, or you want
to use a different mechanism, like using `libvirt`, `virtualbox` or
`vagrant`, you can skip entirely this section.

### Installing the dependencies

We will use `qemu-system-x86_64` and the OVMF firmware to deploy UEFI
nodes, and `socat` and `dnsmasq` to build a local network where our
nodes can communicate.

```bash
zypper in qemu-x86 qemu-ovmf-x86_64 socat dnsmasq
```

We also need the last Kubic image available. You can get it from the
[official page](https://kubic.opensuse.org/), or you can simply do
this:

```bash
wget http://download.opensuse.org/tumbleweed/iso/openSUSE-Kubic-DVD-x86_64-Current.iso
```

Kubic is build on top of Tumbleweed, to this image will be different
each time.

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
             --dhcp-host=00:00:00:11:11:11,10.0.3.101,master \
             --dhcp-host=00:00:00:22:22:22,10.0.3.102,worker1 \
             --dhcp-host=00:00:00:33:33:33,10.0.3.103,worker2 \
             --host-record=master,10.0.3.101
```

This command will deliver IPs into the interface `vmlan` from the
range 10.0.3.100 to 10.0.3.200. The service will ignore the petitions
from the local host and the `em1` interface. If your interfaces are
named differently, you will need to adjust the command accordingly.

The hostnames `master`, `worker1` and `worker2` will be assigned based
on the MAC address, and `master` name will be always resolved to
10.0.3.101. This will simplify the configuration of the salt-minion
later.

### Installing MicoOS for Kubic

Now we can launch two nodes. One will be used for the control plane,
and will be assigned with the `master` hostname, and the other will be
the first worker.

In the same directory where our Kubic ISO image is living, we can
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
    -cdrom openSUSE-Kubic-*.iso \
    -hda hda-node${i}.qcow2 \
    -drive if=pflash,format=raw,unit=0,readonly,file=./ovmf-x86_64-code.bin \
    -drive if=pflash,format=raw,unit=1,file=./ovmf-x86_64-vars-${i}.bin \
    -smp 2 \
    -boot d &
done
```

In the first node (`master`) we will install the System Role named
'Kubic Admin Node'. This will install CRI-O, `kubeadn` and `kubicctl`,
together with `salt-master`.

For the second node (`worker1`) we will choose the System Role 'Kubic
Worker Node'.

If you are not sure about the name of the node, check it launching
xterm (Ctrl-Shift-Alt x). As both process are in background, the order
is not always the same.

### Kubic control plane installation

<!-- With both nodes installed, we can now install Kubic with Flannel via -->
<!-- `kubicctl`. We can try with Cilium, but this is still in alpha, and -->
<!-- sometime the registry contains different image versions that the one -->
<!-- required by YAML declaration. Eventually Cilium will be the -->
<!-- recommended option. -->

<!-- First we need to be sure that the Flannel YAML document is available -->
<!-- in the system: -->

<!-- ```bash -->
<!-- transactional-update pkg install flannel-k8s-yaml -->
<!-- reboot -->
<!-- ``` -->

<!-- Do not forget to reboot in order to have the changes available. -->

<!-- Now, in the `master` node all that needs to be done is -->

<!-- ```bash -->
<!-- kubicctl init --pod-network flannel --adv-addr 10.0.3.101 -->
<!-- ``` -->

<!-- As `flannel` is the default network pod configuration, we can omit -->
<!-- this last parameter. -->

<!-- If you want to try directly the Cilium configuration, you can check -->
<!-- that `cilium-k8s-yaml` package is installed and run instead: -->

<!-- ```bash -->
<!-- kubicctl init --pod-network cilium -->
<!-- ``` -->

For now we cannot use `kubectl` to setup the control plane, as we have
in the `master` VM two interfaces, one that is for the internal
network (`ens3`) and other that is used to connect to the host machine
(`ens4`). This second interface is the same in all QEMU VMs, so it
cannot be used for other communications that are not between the VM
and the host.

The problem is that we cannot guarantee that `kubeadm` will use this
second interface to advertise the `kube-apiserver` service if we do not
use the correct parameters. There is a patch WIP to `kubicctl` that
will pass the correct parameter to `kubeadm`, but meanwhile we need to
manually install the control plane.

We will start with `kubeadm`, that will orchestrate in installation of
the kubernetes admin node:

```bash
kubeadm init --apiserver-advertise-address 10.0.3.101 \
  --cri-socket=/run/crio/crio.sock \
  --pod-network-cidr=10.244.0.0/16
```

The first IP reference where we want to announce the `kube-apiserver`,
that will correspond to the IP of `ens3` in the VM.

Because the command is long, you can copy a paste is via `ssh` to the
`master` node:

```bash
ssh root@localhost -p 10022
```

We will now copy the `admin.conf` configuration in the `root` user:

```bash
mkdir -p $HOME/.kube
sudo cp -i /etc/kubernetes/admin.conf $HOME/.kube/config
sudo chown $(id -u):$(id -g) $HOME/.kube/config
```

With this configuration in place, we can set the pod network. In this
case we will configure the flannel option. Check if the package
`flannel-k8s-yaml` is installed, if not install it and reboot to
enable the changes:

```bash
transactional-update pkg install flannel-k8s-yaml
reboot
```

With those definitions in place, we can now install the network pod:

```bash
kubectl apply -f /usr/share/k8s-yaml/flannel/kube-flannel.yaml
```

Optionally, we can install and configure `kured`:

```bash
kubectl apply -f /usr/share/k8s-yaml/kured/kured.yaml
echo 'REBOOT_METHOD=kured' > /etc/transactional-update.conf
```

### Joining the first worker

Once the service is installed we need to make sure that `salt-minion`
is working on the `worker1` node. So first we need to be sure that
from `worker1` we can see `master`. A simple `ping master` will do. If
so, we can now start the minion in `worker1`:

```bash
echo "master: master" > /etc/salt/minion.d/master.conf
systemctl enable --now salt-minion.service
```

Again, to copy and paste the commands we can ssh into `worker1`:

```bash
ssh root@localhost -p 20022
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
master    Ready    master   11m   v1.14.1
worker1   Ready    <none>   56s   v1.14.1
```

## Provisioning a Kubic worker with Yomi

The first worker was allocated via the Kubic DVD image. This is
reasonable for small clusters, but we can simplify the work if we can
install MicroOS on new nodes using SaltStack.

Yomi is a set of salt states that will allows the provisioning of
systems from the command line, via salt. We will need to boot the new
nodes using a JeOS image that contains a salt-minion service, that
later can be controlled from the `master` node, that is where
`salt-master` is installed.

### Installing yomi-formula in the master node

Before using Yomi we will need to install the Yomi states and
optionally configure the `salt-master` service to simplify the
operation.

All the following actions need to be done in the `master` node. As
Yomi is still not living in Factory, we need to add the home
repository before installing it.

```bash
zypper ar -g -f \
  https://download.opensuse.org/repositories/home:/aplanas/openSUSE_Factory/ \
  yomi-formula
transactional-update pkg install --allow-vendor-change yomi-formula
reboot
```

This will replace the `salt-master` component with a newer one. We can
skip this replacement once `salt-standalone-formulas-configuration`
arrives Factory.

### Booting the new worker

We are going to boot the new worker using a different image. One that
is based on JeOS and contains the `salt-minion` already there.

The image is placed in this
[repository](https://download.opensuse.org/repositories/home:/aplanas:/Images/images/iso/),
you can `wget` it, but if you have `osc` installed you can also
download it directly:

```bash
rm openSUSE-Tumbleweed-JeOS*.iso
osc getbinaries home:aplanas:Images openSUSE-Tumbleweed-JeOS:Live images x86_64
mv binaries/*.iso .
rm -fr binaries
```

We can boot the new node, now using this smaller image:

```bash
# Remove the node fingerprint if needed
ssh-keygen -R [localhost]:30022 -f ~/.ssh/known_hosts
# Create the QCOW2 image if needed
[ -e hda-node3.qcow2 ] || qemu-img create -f qcow2 hda-node3.qcow2 50G
cp -af ovmf-x86_64-vars.bin ovmf-x86_64-vars-3.bin
qemu-system-x86_64 -m 2048 -enable-kvm \
  -netdev socket,id=vmlan,mcast=230.0.0.1:1234 \
  -device virtio-net-pci,netdev=vmlan,mac=00:00:00:33:33:33 \
  -netdev user,id=net0,hostfwd=tcp::30022-:22 \
  -device virtio-net-pci,netdev=net0,mac=10:00:00:33:33:33 \
  -cdrom openSUSE-Tumbleweed-JeOS*.iso \
  -hda hda-node3.qcow2 \
  -drive if=pflash,format=raw,unit=0,readonly,file=./ovmf-x86_64-code.bin \
  -drive if=pflash,format=raw,unit=1,file=./ovmf-x86_64-vars-3.bin \
  -smp 2 \
  -boot d &
```

`dnsmasq` will assign the host name to `worker2`, and the IP
10.0.3.103 in the `ens3` interface. Also salt-minion is already
present and running, with a minion ID of `00:00:00:33:33:33`.

We can go to the master and accept the new key from the minion. We
will learn how to avoid this step later:

```bash
salt-key -A
```

### Setting the pillars

We need to set the pillar data that Yomi will use to make a new
installation. This data will describe installation details how the
hard disk partition layout, the different packages that will be
installed or the services that will be enabled before booting.

The packages `yomi-formula` already provides and example for a MicroOS
installation, so we can use it as a template.

As today the `/srv` directory is part of the non-writable subvolume in
MicroOS (the next MicroOS version will fix that), so for this example
we need to add a new place where pillars are living: 

```bash
cp /usr/share/yomi/pillar.conf /etc/salt/master.d/
systemctl restart salt-master.service
```

This will add a new configuration file that will make
`/usr/share/yomi/pillar` available for salt. Now we can start the
provisioning of the new node:

```bash
salt '00:00:00:33:33:33' state.apply
```

Once the node is back, we can proceed as usual:

```bash
kubicctl node add 00:00:00:33:33:33
kubectl get nodes
```

## Advanced configuration

### Autosign via UUID

The JeOS image that contains `salt-minion` have already some grains
that publish some UUIDs from a restricted list. We can use this
information from the `salt-master` to recognize nodes that are ready
to be installed, and avoid the acceptance of the key in the master.

You can enable this feature copying the configuration snipped that
comes from the `yomi-formula` package and restarting the server:

```bash
cp /usr/share/yomi/autosign.conf /etc/salt/master.d/
systemctl restart salt-master.service
```

Now we can skip the `salt-key -A` for nodes booted from JeOS.

### Salt-API and monitoring the installation

We can use the `monitor` CLI tool to inspect the installation of the
nodes. This tool analyze the event stream, and this require the
configuration of `salt-api`:

```bash
cp /usr/share/yomi/salt-api.conf /etc/salt/master.d/
systemctl restart salt-master.service
```

Use this configuration as an example to understand Yomi's features, as
is not using SSL, and the default user and password is located in
`/usr/share/yomi/user-list.txt` in plain text.

Change in the pillars the `config` section, so you have this:

```yaml
config:
  events: yes
```

Now for each state in Yomi, a two events will be launched. One will
indicate the moment that the state is starting to run, and other will
signalize the success or fail of the event. We can monitor them with:

```bash
export SALTAPI_URL=http://localhost:8000
export SALTAPI_EAUTH=file
export SALTAPI_USER=salt
export SALTAPI_PASS=linux

srv/monitor -r -y
```
