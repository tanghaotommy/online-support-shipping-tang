#!/usr/bin/env python

import urllib
import json
import os
import requests

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = makeWebhookResult(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

@app.route('/smarthome', methods=['POST'])
def smarthome():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = makeResponse(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def makeResponse(req):
	action = req.get("result").get("action")
	result = req.get("result")
	parameters = result.get("parameters")
	res = {}

	if action == "action.openfrontdoor":
		print("Open Front Door!")
		content = {
		"Type": "OpenDoor"
		}
		r = requests.post("http://localhost/order.php", data=json.dumps(content))
		if r.json().get("Status") == 0:
			speech = "Your front door is opened!"
		else:
			speech = "Sorry, I meet some errors. Please try again later!"

	if action == "action.sendalert":
		print("Send Alert!")
		content = {
		"Type": "SendAlert"
		}
		r = requests.post("http://localhost/order.php", data=json.dumps(content))
		if r.json().get("Status") == 0:
			speech = "I have set the beep running!"
		else:
			speech = "Sorry, I meet some errors. Please try again later!"
		facebook = {
  		"facebook": {
    	"attachment": {
      		"type": "image",
      		"payload": {
        		"url": "http://54.183.198.179/UploadedFaceImages/1483855032.jpg"
      		}
    	}
  		}
		}
		res["data"] = facebook

	if action == "status.all":
		print("Check current status")
		content = {
		"Type": "HomeStatus"
		}
		r = requests.post("http://localhost/status.php", data=json.dumps(content))
		if r.json().get("Status") == 0:
			speech = "Your home is all right!"
			res["data"] = r.json().get("Content")
		else:
			speech = "Sorry, I meet some errors. Please try again later!"

	if action == "action.turnofflights":
		location = parameters.get("Location")
		if location == "":
			content = {
			"Type": "TurnOffLight",
			}
			r = requests.post("http://localhost/order.php", data=json.dumps(content))
			if r.json().get("Status") == 0:
				print("Turn off the lights!")
				speech = "I have turned off the lights!"
			else:
				speech = "Sorry, I meet some errors. Please try again later!"
		else:
			content = {
			"Type": "TurnOffLight",
			"Location": location
			}
			r = requests.post("http://localhost/order.php", data=json.dumps(content))
			if r.json().get("Status") == 0:
				print("Turn off the lights!" + location)
				speech = "I have turned off the lights in the " + location + " !"
			else:
				speech = "Sorry, I meet some errors. Please try again later!"

	if action == "action.turnonlights":
		location = parameters.get("Location")
		if location == "":
			content = {
			"Type": "TurnOnLight",
			}
			r = requests.post("http://localhost/order.php", data=json.dumps(content))
			if r.json().get("Status") == 0:
				print("Turn on the lights!")
				speech = "I have turned on the lights!"
			else:
				speech = "Sorry, I meet some errors. Please try again later!"
		else:
			content = {
			"Type": "TurnOnLight",
			"Location": location
			}
			r = requests.post("http://localhost/order.php", data=json.dumps(content))
			if r.json().get("Status") == 0:
				print("Turn on the lights!" + location)
				speech = "I have turned on the lights in the " + location + " !"
			else:
				speech = "Sorry, I meet some errors. Please try again later!"

	print("Response:")
	print(speech)

	res["speech"] = speech
	res["displayText"] = speech
	res["source"] = "apiai-onlinestore-shipping"

	return res;

def makeWebhookResult(req):
    if req.get("result").get("action") != "shipping.cost":
        return {}
    result = req.get("result")
    parameters = result.get("parameters")
    zone = parameters.get("shipping-zone")

    cost = {'Europe':100, 'North America':200, 'South America':300, 'Asia':400, 'Africa':500}

    speech = "The cost of shipping to " + zone + " is " + str(cost[zone]) + " euros."

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        #"data": {},
        # "contextOut": [],
        "source": "apiai-onlinestore-shipping"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    print "Starting app on port %d" % port

    app.run(debug=False, port=port, host='0.0.0.0')
