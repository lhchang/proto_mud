from ryu.base import app_manager
from ryu.ofproto import ofproto_v1_3
from ryu.controller import ofp_event
from ryu.controller.handler import set_ev_cls
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from flask import Flask, jsonify, request
import json
import requests
import threading

#creates the application object as an instance of class Flask, __name__ is predefined, set to the name of the module in which it is used
app = Flask(__name__) 


class MudController(app_manager.RyuApp):
	OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
	def __init__(self, *args, **kwargs):
		super(MudController, self).__init__(*args, **kwargs)
		app.run(debug=True)
		
		
	@app.route('/sendMudUrl', methods=['POST'])
	def receive_mud_url():
		data = request.data

		# data should be in json format containing URL and MAC address?
		jsonData = json.loads(data)
		device_mac =  jsonData['mac']
		mud_url = jsonData['mud_url']
		#response = requests.get(mud_url)
		#if response.status_code == 200:
			
			# get JSON of the MUD file
			# YANG? Parse and then add flow rules?

		#	return 'Success\n'

		return 'Bad\n'

	@set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	def tester(self,ev):
		print 'hi'
		
		


	
