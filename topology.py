#!/usr/bin/env python3
"""
topology.py
Multi-Switch Linear Topology for Flow Table Analyzer
Course: UE24CS252B - Computer Networks

Topology:
    h1 -- s1 -- s2 -- s3 -- h4
           |     |
           h2    h3

3 switches, 4 hosts, linear core with two dangling hosts.
Run: sudo python3 topology.py
"""

from mininet.net import Mininet
from mininet.node import RemoteController, OVSSwitch
from mininet.link import TCLink
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def build_topology():
    net = Mininet(
        controller=RemoteController,
        switch=OVSSwitch,
        link=TCLink,
        autoSetMacs=True
    )

    info("*** Adding controller (POX on 127.0.0.1:6633)\n")
    c0 = net.addController("c0", controller=RemoteController,
                            ip="127.0.0.1", port=6633)

    info("*** Adding switches\n")
    s1 = net.addSwitch("s1")
    s2 = net.addSwitch("s2")
    s3 = net.addSwitch("s3")

    info("*** Adding hosts\n")
    h1 = net.addHost("h1", ip="10.0.0.1/24")
    h2 = net.addHost("h2", ip="10.0.0.2/24")
    h3 = net.addHost("h3", ip="10.0.0.3/24")
    h4 = net.addHost("h4", ip="10.0.0.4/24")

    info("*** Adding links\n")
    # Core linear path: s1 -- s2 -- s3
    net.addLink(s1, s2, bw=100, delay="5ms")
    net.addLink(s2, s3, bw=100, delay="5ms")

    # Hosts
    net.addLink(h1, s1, bw=100, delay="1ms")
    net.addLink(h2, s1, bw=100, delay="1ms")
    net.addLink(h3, s2, bw=100, delay="1ms")
    net.addLink(h4, s3, bw=100, delay="1ms")

    info("*** Starting network\n")
    net.build()
    c0.start()
    s1.start([c0])
    s2.start([c0])
    s3.start([c0])

    info("\n")
    info("=" * 60 + "\n")
    info("  Topology ready!\n")
    info("  Hosts   : h1(10.0.0.1)  h2(10.0.0.2)\n")
    info("            h3(10.0.0.3)  h4(10.0.0.4)\n")
    info("  Switches: s1 -- s2 -- s3\n")
    info("=" * 60 + "\n\n")
    info("  Useful Mininet CLI commands:\n")
    info("    pingall            -- test all-pairs connectivity\n")
    info("    h1 ping h4 -c 5   -- ping from h1 to h4 (5 packets)\n")
    info("    h1 iperf h4 &     -- throughput test\n")
    info("    dpctl dump-flows  -- show flows on all switches\n")
    info("    nodes / net       -- show topology\n")
    info("=" * 60 + "\n\n")

    CLI(net)

    info("*** Stopping network\n")
    net.stop()

if __name__ == "__main__":
    setLogLevel("info")
    build_topology()
