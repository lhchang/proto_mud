import json
import requests
from webob import Response
import eventlet

import mud_parser

from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

mud_controller_instance_name = 'mud_controller_api'



class MudController(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(MudController, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        wsgi = kwargs['wsgi']
        wsgi.register(MudApi,
                      {mud_controller_instance_name: self})

    # Configure connected switches with default rules

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        print "mac address of switch %s" % str(datapath)

        req = parser.OFPSetConfig(datapath, ofproto_v1_3.OFPC_FRAG_NORMAL, 1024)
        datapath.send_msg(req)
        print 'Configuration parameters set up: ofproto_v1_3.OFPC_FRAG_NORMAL, 1024'
        print 'Adding default flows for DHCP, DNS, and NTP...'

        match = parser.OFPMatch() # table miss
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

        match = parser.OFPMatch(eth_type=0x0800,ip_proto=17,udp_src=68,udp_dst=67) #DHCP discovery/request
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL,0)]
        self.add_flow(datapath, 10, match, actions)

        match = parser.OFPMatch(eth_type=0x0800, ip_proto=17, udp_src=67, udp_dst=68)  # DHCP offer/ack
        actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL, 0)]
        self.add_flow(datapath, 10, match, actions)

        match = parser.OFPMatch(eth_type=0x0800,ip_proto=17,udp_src=53) #DNS
        actions=[parser.OFPActionOutput(ofproto.OFPP_NORMAL,0)]
        self.add_flow(datapath,10,match,actions)

        match = parser.OFPMatch(eth_type=0x0800,ip_proto=17,udp_src=123) #NTP
        self.add_flow(datapath,10,match,actions)


    # function to add flow rules

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


    '''
    Function below is taken from simple_switch_13.py, acts as a simple learning L2 switch -- debugging purposes
    '''
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
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

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp and ipv6 packet
            return
        dst = eth.dst
        src = eth.src

        dpid = datapath.id
        self.mac_to_port.setdefault(dpid, {})

        self.logger.info("packet in %s %s %s %s", dpid, src, dst, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)




class MudApi(ControllerBase):
    def __init__(self, req, link, data, **config):
        super(MudApi, self).__init__(req, link, data, **config)
        self.mud_controller_app = data[mud_controller_instance_name]

    # receive forwarded DHCP MUD URL
    @route('sendmud','/sendMud',methods=['POST'])
    def sendMudUrl(self,req,**kwargs):
        recvdData = req.json
        device_mac = recvdData['mac']  # get device mac - we use this to push rules
        mud_url = recvdData['mud_url'] # get mud_url, to fetch associated mud file
        headers = {'Accept':'application/mud+json', 'Accept-Language':'en', 'User-Agent':'thesisMudController/1.0'}

        # verify=False temporarily for testing on local htts server
        try:
            response = requests.get(mud_url, verify=False, headers=headers, timeout=3)
            if response.status_code == 200:
                mud_str = response.content # get string representation of MUD file
                mud_file = json.loads(mud_str) # change it to JSON format for parsing
                mp = mud_parser.MudParser(mud_file)

                # This needs to be changed
                #if mp.getFromFlowIds() == False:
                #    return Response(status=400,body='Invalid MUD file - Failed to insert rules')
        except requests.exceptions.Timeout:
            # return 400 if bad request
            return Response(status=400,body='400: Bad URL\n')









	
