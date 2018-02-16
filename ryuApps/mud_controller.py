import json
import requests
from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.app.wsgi import ControllerBase, WSGIApplication, route


mud_controller_instance_name = 'mud_controller_api'



class MudController(app_manager.RyuApp):

    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super(MudController, self).__init__(*args, **kwargs)
        self.switches = {}
        wsgi = kwargs['wsgi']
        wsgi.register(MudApi,
                      {mud_controller_instance_name: self})

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        print 'hi'


class MudApi(ControllerBase):

    def __init__(self, req, link, data, **config):
        super(MudApi, self).__init__(req, link, data, **config)
        self.mud_controller_app = data[mud_controller_instance_name]

    @route('simpleswitch','/asdf',methods=['GET'])
    def holla(self,req,**kwargs):
        print 'hi'



	
