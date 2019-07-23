# Appendix: How to use QEMU to test Yomi

We can use libvirt, VirtualBox or real hardware to test Yomi. In this
appendix we will give the basic instructions to setup QEMU with KVM to
create a local network that will enable the communication of the nodes
between each other, and with the guest.

## General overview

We will use `qemu-system-x86_64` and the OVMF firmware to deploy UEFI
nodes, and `socat` and `dnsmasq` to build a local network where our
nodes can communicate.

With QEMU we usually need to create some bridges and tun/tap
interfaces that enable the communication between the local
instances. To provide external access to those instances, we also
usually need to enable the masquerading via `iptables`, and
`ip_forward` via `sysctl` in out host. But using `socat` and `dnsmasq`
we can avoid this.

For this to work we will need two interfaces in the virtual
machine. One will be owned by QEMU, that will use the user networking
(SLIRP) back-end. In this network mode, the interface will have always
the IP 10.0.2.15 in the VM side, and the host is reachable via the
10.0.2.2 IP. There is also an internal DNS under the IP 10.0.2.3, that
is managed by QEMU and cannot be configured.

SLIRP is optional and more complicated QEMU deployments disable this
back-end by default. But for us is an easy way to have a connection
between the VM and the host.

If we maintain SLIPR operational, all the VMs will have the same IP,
and all of them will see the host machine via the same IP too, but
they cannot see each other. To resolve this we can add a second
virtual interface in the VM, that using multi-cast, will be used as a
communication channel between the VMs.

We will need to use to external tools to enable this multi-cast
communication. One, `socat`, will create a new virtual interface named
`vmlan` in the host, where all the VMs will be connected to. And the
other is `dnsmasq`, that will be used as a local DHCP / DNS server
that will work on this new interface.

### Creating the local network

First we will need to install both tools:

```bash
zypper in socat dnsmasq
```

Now we need to use `socat` to create a new virtual interface named
`vmlan`, that will expose the IP 10.0.3.1 to the host. At the other
side we will have the multicast socket from QEMU.

```bash
sudo socat \
  UDP4-DATAGRAM:230.0.0.1:1234,sourceport=1234,reuseaddr,ip-add-membership=230.0.0.1:127.0.0.1 \
  TUN:10.0.3.1/24,tun-type=tap,iff-no-pi,iff-up,tun-name=vmlan
```

If you see the error `Network is unreachable`, check if all the
interfaces have an IP assigned (this can be the case when running
inside a VM). But if the error message is `Device or resource busy`,
check that there is not a previous `socat` process running for the
same connection.

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

### Connecting QEMU to the new network

We can now launch QEMU to have two interfaces. One will be connected
to the new `vmlan` network, via the multi-cast socket option, and the
other interface will be connected to the host machine.

Because we will use UEFI, we will need first to copy the OVMF firmware
locally.

```bash
cp /usr/share/qemu/ovmf-x86_64-code.bin .
cp /usr/share/qemu/ovmf-x86_64-vars.bin .
```

Now we can launch QEMU:

```bash
# Local copy for the variable OVMF file
cp -af ovmf-x86_64-vars.bin ovmf-x86_64-vars-node.bin

# Create the file that will be used as a hard-disk
qemu-img create -f qcow2 hda-node.qcow2 50G

qemu-system-x86_64 -m 2048 -enable-kvm \
  -netdev socket,id=vmlan,mcast=230.0.0.1:1234 \
  -device virtio-net-pci,netdev=vmlan,mac=00:00:00:11:11:11 \
  -netdev user,id=net0,hostfwd=tcp::10022-:22 \
  -device virtio-net-pci,netdev=net0,mac=10:00:00:11:11:11 \
  -cdrom *.iso \
  -hda hda-node.qcow2 \
  -drive if=pflash,format=raw,unit=0,readonly,file=./ovmf-x86_64-code.bin \
  -drive if=pflash,format=raw,unit=1,file=./ovmf-x86_64-vars-node.bin \
  -smp 2 \
  -boot d &
```

The first interface will be connected to the `vmlan` via a multi-cast
socket. The second interface will be the SLIRP user network mode, that
will be connected to the host. We also forward the local port `10022`
to the port `22` in the VM. So we can SSH into the node with:

```bash
ssh root@localhost -p 10022
```
