# This director contains the SDN applications to be run ontop of Ryu

## To be completed...

- mud_controller: SDN application that retrieves and pushes mud flows into SDN switches
	- DNS resolution of flows
	- add flows
	- keep track of connected flows
	- provide APIs?
- traffic monitor and detector: will perform statistical analysis on flows (SEE PAPER "SDN-based DDoS Attack Detection with Cross-Plane
Collaboration and Lightweight Flow Monitoring" by Yang et al)
- ~~mud_parser: contains class that takes in a mud file and breaks it into MUD info and ACL info. Contains data structures of parsed flows to be used to convert into flow rules~~
