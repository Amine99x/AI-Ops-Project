#!/usr/bin/env python3
from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info

def topology():
    net = Mininet(controller=Controller, switch=OVSKernelSwitch, link=TCLink)
    net.addController('c0')

    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    s3 = net.addSwitch('s3')

    h1 = net.addHost('h1', ip='10.0.0.1/24')
    h2 = net.addHost('h2', ip='10.0.0.2/24')
    h3 = net.addHost('h3', ip='10.0.0.3/24')

    # Main path = limited bandwidth → easy congestion
    net.addLink(h1, s1, bw=50, delay='2ms')
    net.addLink(h3, s1, bw=50, delay='2ms')
    net.addLink(h2, s2, bw=50, delay='2ms')
    net.addLink(s1, s2, bw=10, delay='20ms')   # ← congestion happens here
    # Backup path (higher bandwidth)
    net.addLink(s1, s3, bw=50, delay='5ms')
    net.addLink(s3, s2, bw=50, delay='5ms')

    net.start()

    # Clean old flows
    for sw in [s1, s2, s3]:
        sw.cmd(f'ovs-ofctl del-flows {sw.name}')

    # Primary path flows (low priority)
    s1.cmd('ovs-ofctl add-flow s1 priority=200,ip,nw_dst=10.0.0.2,actions=output:3')
    # (adjust output numbers if needed after checking ovs-vsctl show)

    info('*** Topologie 3 switches prête (s1-s2 principal | s1-s3-s2 alternatif) ***\n')
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()