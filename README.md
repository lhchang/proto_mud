# Proto MUD: A minimalistic and incomplete implementation of Manufacturer Usage Descriptions for the purpose of Laurence Chang 2018 Thesis
https://tools.ietf.org/html/draft-ietf-opsawg-mud-15

### Pre-requisites
The following are to be installed before execution:

- Ryu Controller
	- Instructions for installation: <https://github.com/osrg/ryu>
- Mininet: For testing
	- Instructions for installation <http://mininet.org/download/>
		- Please follow Method 2 when installing. Install everything such that OVS (Open vSwitch) will also be installed.
- staticDHCPd
	- Install <https://github.com/flan/staticdhcpd>
- bind9 DNS server
	- apt-get install bind9

- required libraries
	- requests
	- json
	- socket
	- ~~pyang~~
	- ~~pyangbind~~

### Organization
Will need to eventually transition and replace mud_controller.py with mud_controller_v2.py



