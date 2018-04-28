import pprint as pp
import uuid
import requests
import json

import mud_parser

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib.packet import packet
from ryu.lib.packet import dhcp
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

class MudController(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(MudController, self).__init__(*args, **kwargs)
        self.dpid_to_mac = {1:'aa:bb:cc:dd:ee:00', 2:'aa:bb:cc:dd:ee:01'} # for gateway access... (hardcoded)
        self.mac_to_port = {}

    """
    Exchange of OFPT_FEATURES_REQUEST (see page 53 of OF 1.3 specification)
    We install "default rules" for DHCP, DNS, NTP here
    """
    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath #datapath of the switch
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        print 'Connected to switch at datapath %s' % str(datapath.id)
        req = parser.OFPSetConfig(datapath, ofproto_v1_3.OFPC_FRAG_NORMAL, 1024)
        print 'Configuration parameters set up: ofproto_v1_3.OFPC_FRAG_NORMAL, 1024'
        datapath.send_msg(req)

        if datapath.id == 3: # "Internet" should work as normal
            match = parser.OFPMatch()
            actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
            self.add_flow(datapath, 0, match, actions)

        else:
            match = parser.OFPMatch()  # table miss
            actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                              ofproto.OFPCML_NO_BUFFER)]
            self.add_flow(datapath, 0, match, actions)
            print 'ADDED TABLE_MISS RULE'

            match = parser.OFPMatch(eth_type=0x0800, ip_proto=17, udp_src=68, udp_dst=67)  # DHCP discovery/request
            self.add_flow(datapath, 10, match, actions)
            print 'ADDED DHCP REQUEST RULE' # All DHCP discovery should go through controller for MUD processing

            match = parser.OFPMatch(eth_type=0x0800, ip_proto=17, udp_src=67, udp_dst=68)  # DHCP offer/ack
            actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL,0)]
            self.add_flow(datapath, 10, match, actions)
            print 'ADDED DHCP OFFER/ACK RULE'

            match = parser.OFPMatch(eth_type=0x0806, eth_dst='ff:ff:ff:ff:ff:ff')
            actions = [parser.OFPActionOutput(ofproto.OFPP_FLOOD)]
            self.add_flow(datapath, 10, match, actions)
            print 'Added Flood Rule'

            match = parser.OFPMatch(eth_type=0x0800, ip_proto=17, udp_dst=53)
            actions = [parser.OFPActionOutput(3)]
            inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
            mod = parser.OFPFlowMod(datapath=datapath, priority=20, match=match, instructions=inst)
            datapath.send_msg(mod)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)
        datapath.send_msg(mod)


    def add_mud_flows(self, device_mac, mudentry, datapath, in_port, priority=0, buffer_id=None, table=0):

        '''
        :param device_mac: the device's mac address
        :param mudentry: mud object
        :param datapath: dpid of the switch device is connected to
        :param in_port: port device is connected to
        :param priority: specify a priority, by default 0
        :param buffer_id: when received packets are buffered on OF switch, indicates its ID if not buffered, OFP_NO_BUFFER is set
        :param table: specify a table, by default None (may need to experiment with tables)
        :return: None
        '''

        toFlows = mudentry.toFlows
        fromFlows = mudentry.fromFlows

        cookie_list = [] # list to maintain "order" of symmetric flows

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = None
        actions = None
        inst = None

        # to-device MUD flows
        for flow in toFlows:
            sourceAddr = toFlows[flow][0]
            proto = toFlows[flow][1]
            src_port = toFlows[flow][2]
            dst_port = toFlows[flow][3]

            print sourceAddr,proto,src_port,dst_port

            if proto == 6:
                # local and remote ports specified
                if src_port != '*' and dst_port != '*':
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_dst=device_mac, ipv4_src=sourceAddr,
                                            tcp_src=src_port, tcp_dst=dst_port)

                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL,0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]

                # local port not specified, remote port specified
                elif src_port == '*' and dst_port != '*':
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_dst=device_mac, ipv4_src=sourceAddr,
                                            tcp_dst=dst_port)

                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

                # local port specified, remote port not specified
                elif src_port != '*' and dst_port == '*':
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_dst=device_mac, ipv4_src=sourceAddr,
                                            tcp_src=src_port)
                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

                # any ports specified
                else:
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_dst=device_mac, ipv4_src=sourceAddr)
                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

            elif proto == 17:
                # local and remote ports specified
                if src_port != '*' and dst_port != '*':
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_dst=device_mac, ipv4_src=sourceAddr,
                                            udp_src=src_port, udp_dst=dst_port)

                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

                # local port not specified, remote port specified
                elif src_port == '*' and dst_port != '*':
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_dst=device_mac, ipv4_src=sourceAddr,
                                            udp_dst=dst_port)

                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

                # local port specified, remote port not specified
                elif src_port != '*' and dst_port == '*':
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_dst=device_mac, ipv4_src=sourceAddr,
                                            udp_src=src_port)
                # any ports specified
                else:
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_dst=device_mac, ipv4_src=sourceAddr)
                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
            else:
                match = parser.OFPMatch(eth_type=0x0800, eth_dst=device_mac, ipv4_src=sourceAddr)
                actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL,0)]
                inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]

            flow_cookie = uuid.uuid4().int>>64
            cookie_list.append(flow_cookie)
            mod = parser.OFPFlowMod(datapath=datapath, priority=20,match=match, instructions=inst, cookie=flow_cookie)
            datapath.send_msg(mod)

        # from-device MUD flows
        cookie_index = 0
        for flow in fromFlows:
            dstAddr = fromFlows[flow][0]
            proto = fromFlows[flow][1]
            src_port = fromFlows[flow][2]
            dst_port = fromFlows[flow][3]

            if proto == 6:
                if src_port != '*' and dst_port != '*':
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_src=device_mac, ipv4_dst=dstAddr,
                                            tcp_src=src_port, tcp_dst=dst_port)

                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL,0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,actions)]

                # local port not specified, remote port specified
                elif src_port == '*' and dst_port != '*':
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_src=device_mac, ipv4_dst=dstAddr,
                                            tcp_dst=dst_port)

                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

                # local port specified, remote port not specified
                elif src_port != '*' and dst_port == '*':
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_src=device_mac, ipv4_dst=dstAddr,
                                            tcp_src=src_port)
                # any ports specified
                else:
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_src=device_mac, ipv4_dst=dstAddr)
                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

            elif proto == 17:
                # local and remote ports specified
                if src_port != '*' and dst_port != '*':
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_src=device_mac, ipv4_dst=dstAddr,
                                            udp_src=src_port, udp_dst=dst_port)

                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

                # local port not specified, remote port specified
                elif src_port == '*' and dst_port != '*':
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_src=device_mac, ipv4_dst=dstAddr,
                                            udp_dst=dst_port)

                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

                # local port specified, remote port not specified
                elif src_port != '*' and dst_port == '*':
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_src=device_mac, ipv4_dst=dstAddr,
                                            udp_src=src_port)
                # any ports specified
                else:
                    match = parser.OFPMatch(eth_type=0x0800, ip_proto=proto, eth_src=device_mac, ipv4_dst=dstAddr)
                    actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
                    inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

            else:
                match = parser.OFPMatch(eth_type=0x0800, eth_src=device_mac, ipv4_dst=dstAddr)
                actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
                inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]

            sym_cookie = cookie_list[cookie_index]-1
            cookie_index += 1
            mod = parser.OFPFlowMod(datapath=datapath, priority=20, match=match, instructions=inst, cookie=sym_cookie)
            datapath.send_msg(mod)



        # Gateway Rules - specific to the gateway and device communication
        # We "know" port 3 is always the "wan"
        # device-to-gateway rule
        match = parser.OFPMatch(eth_type=0x0806, eth_src=device_mac,eth_dst=self.dpid_to_mac[datapath.id])
        actions = [parser.OFPActionOutput(3)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=20, match=match, instructions=inst)
        datapath.send_msg(mod)

        # gateway-to-device rule
        match = parser.OFPMatch(eth_type=0x0806, eth_src=self.dpid_to_mac[datapath.id],eth_dst=device_mac)
        actions = [parser.OFPActionOutput(in_port)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=20, match=match, instructions=inst)
        datapath.send_msg(mod)

        # dns gateway-to-device response rule
        match = parser.OFPMatch(eth_type=0x0800, ip_proto=17, eth_dst=device_mac, udp_src=53)
        actions = [parser.OFPActionOutput(in_port)]
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=20, match=match, instructions=inst)
        datapath.send_msg(mod)




    def __processMUD(self, mudPacket, mudOption, datapath, in_port):
        '''

        :param mudPacket: dhcp packet containing mud option, used for installing flow rules
        :param mudOption: mud option containing URL
        :param datapath: datapath id to push flow to
        :return: Boolean - True for success, False for failure
        '''

        requests.packages.urllib3.disable_warnings()
        mudURL = mudOption.value
        headers = {'Accept': 'application/mud+json', 'Accept-Language': 'en', 'User-Agent': 'MUDController/1.0'}
        device_mac = mudPacket.chaddr

        try:
            response = requests.get(mudURL, verify='server.pem', headers=headers, timeout=3)
            if response.status_code == 200:
                mud_str = response.content # get string representation of MUD file
                mud_file = json.loads(mud_str) # change it to JSON format for parsing
                mud_entry = mud_parser.Mud(mud_file)
                self.add_mud_flows(device_mac, mud_entry, datapath, in_port)

        except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, ValueError) as e:
            print 'Unable to retrieve MUD file: %s' % e
            print 'Forwarding DHCP as normal'
            return None


    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self,ev):
        # If you hit this you might want to increase
        # the "miss_send_length" of your switch
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        ## Get Packet Info
        pkt = packet.Packet(msg.data)

        ## Control flow begins here -- if DHCP we want to process MUD
        if pkt.get_protocols(dhcp.dhcp):
            requestFlag = False
            dhcpPacket = pkt.get_protocols(dhcp.dhcp)[0]
            optionsList = dhcpPacket.options.option_list

            requestClass = None
            mudOption = None

            # Iterate through all the options in the dhcp packet
            for option in optionsList:
                if option.tag == 53:
                    requestClass = option
                    continue
                if option.tag == 161:
                    mudOption = option
                    continue

            # Check if DHCP request, other types we want to go on as normal
            # 0x03 is DHCPREQUEST
            if requestClass.value == '\x03' and mudOption is not None:
                print 'PROCESSING MUD OPTION 161'
                mudObject = self.__processMUD(dhcpPacket, mudOption, datapath, in_port)
                print 'FINISHED PROCESSING MUD'


            # forwardPacket in either case
            actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
            data = pkt
            packet_out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                                in_port=in_port, actions=actions, data=data)
            datapath.send_msg(packet_out)
            print 'PACKET_OUT SENT'

        else:
            # Learning switch mechanism for testing purposes
            eth = pkt.get_protocols(ethernet.ethernet)[0]
            if eth.ethertype == ether_types.ETH_TYPE_LLDP:
                # ignore lldp and ipv6 packet
                return
            dst = eth.dst
            src = eth.src
            dpid = datapath.id
            #self.mac_to_port.setdefault(dpid, {})
            self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

            #learn a mac address to avoid FLOOD next time.
            #self.mac_to_port[dpid][src] = in_port

            #if dst in self.mac_to_port[dpid]:
            #    out_port = self.mac_to_port[dpid][dst]
            #else:
            #    out_port = ofproto.OFPP_FLOOD

            #actions = [parser.OFPActionOutput(out_port)]

            #install a flow to avoid packet_in next time
            #if out_port != ofproto.OFPP_FLOOD:
            #    match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
                # verify if we have a valid buffer_id, if yes avoid to send both
                # flow_mod & packet_out
            #    if msg.buffer_id != ofproto.OFP_NO_BUFFER:
            #        self.add_flow(datapath, 1, match, actions, msg.buffer_id)
            #        return
            #    else:
            #        self.add_flow(datapath, 1, match, actions)

            data = None
            #if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            #    data = msg.data

            #edit 04/18/18
            actions = []

            out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                      in_port=in_port, actions=actions, data=data)
            datapath.send_msg(out)
            print 'Traffic not allowed - dropping and alerting!!!'