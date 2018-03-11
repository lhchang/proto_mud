from mininet.net import Mininet
from mininet.node import Controller
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def startNet():
	net = Mininet(controller=None)

	info( '*** Adding controller\n' )
	net.addController( 'c0' ,controller=RemoteController, ip='127.0.0.1',port=6633)

	# Adding hosts to switch 1
	info( '*** Adding hosts\n' )
	h1 = net.addHost( 'h1', ip='10.0.0.1', mac='00:00:00:00:00:01')
	h2 = net.addHost( 'h2', ip='10.0.0.2', mac='00:00:00:00:00:02')
	info( '*** Adding switch\n' )
	s1 = net.addSwitch( 's1' )
	info( '*** Creating links\n' )
	net.addLink( h1, s1 )
	net.addLink( h2, s1 )

	info( '*** Disabling ipv6\n')
	for h in net.hosts:
		h.cmd('sysctl -w net.ipv6.conf.all.disable_ipv6=1')
		h.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
		h.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")
	for sw in net.switches:
		sw.cmd("sysctl -w net.ipv6.conf.all.disable_ipv6=1")
		sw.cmd("sysctl -w net.ipv6.conf.default.disable_ipv6=1")
		sw.cmd("sysctl -w net.ipv6.conf.lo.disable_ipv6=1")

	info( '*** Starting network\n')
	net.start()
	
	# Open xterm windows to be able to interact with containers
	h1.cmdPrint('xterm -xrm \'XTerm.vt100.allowTitleOps: false\' -T h1 &')
	h2.cmdPrint('xterm -xrm \'XTerm.vt100.allowTitleOps: false\' -T h2 &')
	info( '*** Running CLI\n' )
	CLI( net )
	info( '*** Stopping network' )
	net.stop()



if __name__ == '__main__':
    setLogLevel( 'info' )
    startNet()
