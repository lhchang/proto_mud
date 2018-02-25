from mininet.net import Mininet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.log import setLogLevel, info

def startNet():
	net = Mininet(controller=Controller)

	info( '*** Adding controller\n' )
	net.addController( 'c0' )
	info( '*** Adding hosts\n' )
	h1 = net.addHost( 'h1')
	h2 = net.addHost( 'h2', ip='10.0.0.2' )
	info( '*** Adding switch\n' )
	s3 = net.addSwitch( 's3' )
	info( '*** Creating links\n' )
	net.addLink( h1, s3 )
	net.addLink( h2, s3 )
	info( '*** Starting network\n')
	net.start()
	h1.setMAC("00:00:00:00:00:01","h1-eth0")
	h1.cmdPrint('xterm -xrm \'XTerm.vt100.allowTitleOps: false\' -T h1 &')
	h2.cmdPrint('xterm -xrm \'XTerm.vt100.allowTitleOps: false\' -T h2 &')
	info( '*** Running CLI\n' )
	CLI( net )
	info( '*** Stopping network' )
	net.stop()



if __name__ == '__main__':
    setLogLevel( 'info' )
    startNet()