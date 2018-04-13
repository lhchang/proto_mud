from mininet.net import Mininet
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def startNet():
	net = Mininet(controller=None)

	info('*** Adding controller\n')
	controller = net.addController( 'c0' ,controller=RemoteController, ip='127.0.0.1',port=6633)

	# Adding hosts to switch 1
	info('*** Adding hosts\n')
	h1 = net.addHost( 'h1', ip=None, mac='00:00:00:00:00:01') # iot device 1
	h2 = net.addHost( 'h2', ip=None, mac='00:00:00:00:00:02') # iot device 2
	

	#For testing purposes
	#h1 = net.addHost( 'h1', ip='192.168.1.1/24', mac='00:00:00:00:00:01')
	#h2 = net.addHost( 'h2', ip='192.168.1.2/24', mac='00:00:00:00:00:02')
	#h3 = net.addHost( 'h3', ip='192.168.1.3/24', mac='00:00:00:00:00:03')

	h3 = net.addHost( 'h3', ip=None, mac='00:00:00:00:00:03') # iot device 3
	h4 = net.addHost( 'h4', ip=None, mac='00:00:00:00:00:04') # iot device 4

	server = net.addHost( 'mud-server', ip='192.168.3.2/24', mac='00:00:00:00:00:05' ) # mud-server hosting mudfile
	r1 = net.addHost('r1',mac='AA:BB:CC:DD:EE:FF') # router
	
	info('*** Adding switch\n')
	s1 = net.addSwitch( 's1' )
	s2 = net.addSwitch( 's2' )

	info('*** Creating links\n')
	#subnet 1
	net.addLink(h1,s1) # s1 - port 1
	net.addLink(h2,s1) # s1 - port 2

	#subnet 2
	net.addLink(h3,s2) # s2 - port 1
	net.addLink(h4,s2) # s2 - port 2

	net.addLink(r1,s1) # s1 - port 3
	net.addLink(r1,s2) # s2 - port 3

	info('*** Disabling ipv6\n')
	for h in net.hosts:
		h.cmd('sysctl -w net.ipv6.conf.all.disable_ipv6=1')
		h.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
		h.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")
	for sw in net.switches:
		sw.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
		sw.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
		sw.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

	info('*** Starting network\n')
	net.start()
	
	# Open xterm windows to be able to interact with containers
	#h1.cmdPrint('xterm -xrm \'XTerm.vt100.allowTitleOps: false\' -T h1 &')
	#h2.cmdPrint('xterm -xrm \'XTerm.vt100.allowTitleOps: false\' -T h2 &')
	#h3.cmdPrint('xterm -xrm \'XTerm.vt100.allowTitleOps: false\' -T h3 &')

	info( '*** Setting up router')
	r1.cmd("ifconfig r1-eth0 0")
	r1.cmd("ifconfig r1-eth1 0")
	r1.cmd("ifconfig r1-eth2 0")
	r1.cmd("ifconfig r1-eth0 hw ether AA:BB:CC:DD:EE:00")
	r1.cmd("ifconfig r1-eth1 hw ether AA:BB:CC:DD:EE:01")
	r1.cmd("ifconfig r1-eth2 hw ether AA:BB:CC:DD:EE:02")
	r1.cmd("ip addr add 192.168.1.1/24 brd + dev r1-eth0")
	r1.cmd("ip addr add 192.168.2.1/24 brd + dev r1-eth1")
	r1.cmd("ip addr add 192.168.3.1/24 brd + dev r1-eth2")
	r1.cmd("ip link set r1-eth0 up")
	r1.cmd("ip link set r1-eth1 up")
	r1.cmd("ip link set r1-eth2 up")
	r1.cmd("echo 1 > /proc/sys/net/ipv4/ip_forward")

	r1.cmd("cd ~/Thesis/staticdhcpd/staticDHCPd")
	r1.cmdPrint('xterm -xrm \'XTerm.vt100.allowTitleOps: false\' -T r1 &')

	server.cmd("cd ~/Thesis/proto_mud/ryuApps/tests/webserver")
	server.cmdPrint('xterm -xrm \'XTerm.vt100.allowTitleOps: false\' -T mud-server &')

	info( '*** Running CLI\n' )
	CLI(net)
	info('*** Stopping network')
	net.stop()



if __name__ == '__main__':
    setLogLevel( 'info' )
    startNet()
