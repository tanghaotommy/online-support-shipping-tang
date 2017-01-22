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
	facebook_userId = req.get("sessionId")
	parameters = result.get("parameters")
	res = {}

	if action == "action.register":
		print("New user registers!")
		content = {
			"Type": "register",
			"Id": facebook_userId
		}
		print content
		r = requests.post("http://localhost/register.php", data=json.dumps(content))
		response = r.json()
		if response.get("Status") == 0:
			speech = "You have successfully registered! Welcome, I am now your home assistant! What Can I do for you?"
		else:
			speech = "Sorry, I meet some errors. Please try again later!"
			
	if action == "action.openfrontdoor":
		print("Open Front Door!")
		content = {
		"Type": "OpenDoor",
		"Id": facebook_userId
		}
		r = requests.post("http://localhost/order.php", data=json.dumps(content))
		response = r.json()
		if response.get("Status") == 0:
			speech = "Your front door is opened!"
		elif response.get("Status") == 2:
			speech = "Oh, it seems your are not registered yet. Do you want to register right now?"
			res["contextOut"] = [{"name":"register", "lifespan":2}]
		else:
			speech = "Sorry, I meet some errors. Please try again later!"

	if action == "action.sendalert":
		print("Send Alert!")
		content = {
		"Type": "SendAlert",
		"Id": facebook_userId
		}
		r = requests.post("http://localhost/order.php", data=json.dumps(content))
		response = r.json()
		if response.get("Status") == 0:
			speech = "I have set the beep running!"
		elif response.get("Status") == 2:
			speech = "Oh, it seems your are not registered yet. Do you want to register right now?"
			res["contextOut"] = [{"name":"register", "lifespan":2}]
		else:
			speech = "Sorry, I meet some errors. Please try again later!"

	if action == "action.viewphoto":
		print("ViewPhoto!")
		content = {
			"Type": "ViewPhoto",
			"Id": facebook_userId
		}
		r = requests.post("http://54.183.198.179/order.php", data=json.dumps(content))
		print r.json()
		response = r.json()
		if response.get("Status") == 0:
			if response.get("Content").get("Name") != "null":
				speech = "Oh, " + response.get("Content").get("Name") + "is at your front door!"
			else:
				speech = "There is currently nobody at your front door!"

			facebook = {
  				"facebook": {
    			"attachment": {
      				"type": "image",
      			"payload": {
        			"url": response.get('Content').get('url')
      			}
    		}
  			}
			}
			res["data"] = facebook
		elif response.get("Status") == 2:
			speech = "Oh, it seems your are not registered yet. Do you want to register right now?"
			res["contextOut"] = [{"name":"register", "lifespan":2}]
		else:
			speech = "Sorry, I meet some errors. Please try again later!"

	if action == "action.viewvideo":
		print("ViewVideo!")
		content = {
			"Type": "ViewVideo",
			"Id": facebook_userId
		}
		r = requests.post("http://localhost/order.php", data=json.dumps(content))
		response = r.json()
		if response.get("Status") == 0:
			speech = "Here is a short video of your front door!"
			facebook = {
  				"facebook": {
    			"attachment": {
      				"type": "video",
      			"payload": {
        			"url": r.json().get('Content').get('url')
      			}
    		}
  			}
			}
			res["data"] = facebook
		elif response.get("Status") == 2:
			speech = "Oh, it seems your are not registered yet. Do you want to register right now?"
			res["contextOut"] = [{"name":"register", "lifespan":2}]
		else:
			speech = "Sorry, I meet some errors. Please try again later!"

	if action == "action.sendalert":
		print("Send Alert!")
		content = {
		"Type": "SendAlert",
		"Id": facebook_userId
		}
		r = requests.post("http://localhost/order.php", data=json.dumps(content))
		response = r.json()
		if response.get("Status") == 0:
			speech = "I have set the beep running!"
		elif response.get("Status") == 2:
			speech = "Oh, it seems your are not registered yet. Do you want to register right now?"
			res["contextOut"] = [{"name":"register", "lifespan":2}]
		else:
			speech = "Sorry, I meet some errors. Please try again later!"
		
	if action == "status.all":
		print("Check current status")
		content = {
		"Type": "HomeStatus",
		"Id": facebook_userId
		}
		r = requests.post("http://localhost/status.php", data=json.dumps(content))
		response = r.json()
		if response.get("Status") == 0:
			speech = "Your home is all right!"
			res["data"] = r.json().get("Content")
		elif response.get("Status") == 2:
			speech = "Oh, it seems your are not registered yet. Do you want to register right now?"
			res["contextOut"] = [{"name":"register", "lifespan":2}]
		else:
			speech = "Sorry, I meet some errors. Please try again later!"

	if action == "action.turnofflights":
		location = parameters.get("Location")
		if location == "":
			content = {
			"Type": "TurnOffLight",
			"Id": facebook_userId
			}
			r = requests.post("http://localhost/order.php", data=json.dumps(content))
			response = r.json()
			if response.get("Status") == 0:
				print("Turn off the lights!")
				speech = "I have turned off the lights!"
			elif response.get("Status") == 2:
				speech = "Oh, it seems your are not registered yet. Do you want to register right now?"
				res["contextOut"] = [{"name":"register", "lifespan":2}]
			else:
				speech = "Sorry, I meet some errors. Please try again later!"
		else:
			content = {
			"Type": "TurnOffLight",
			"Id": facebook_userId,
			"Location": location
			}
			r = requests.post("http://localhost/order.php", data=json.dumps(content))
			response = r.json()
			if response.get("Status") == 0:
				print("Turn off the lights!" + location)
				speech = "I have turned off the lights in the " + location + " !"
			elif response.get("Status") == 2:
				speech = "Oh, it seems your are not registered yet. Do you want to register right now?"
				res["contextOut"] = [{"name":"register", "lifespan":2}]
			else:
				speech = "Sorry, I meet some errors. Please try again later!"

	if action == "action.turnonlights":
		location = parameters.get("Location")
		if location == "":
			content = {
			"Type": "TurnOnLight",
			"Id": facebook_userId
			}
			r = requests.post("http://localhost/order.php", data=json.dumps(content))
			response = r.json()
			if response.get("Status") == 0:
				print("Turn on the lights!")
				speech = "I have turned on the lights!"
			elif response.get("Status") == 2:
				speech = "Oh, it seems your are not registered yet. Do you want to register right now?"
				res["contextOut"] = [{"name":"register", "lifespan":2}]
			else:
				speech = "Sorry, I meet some errors. Please try again later!"
		else:
			content = {
			"Type": "TurnOnLight",
			"Id": facebook_userId,
			"Location": location
			}
			r = requests.post("http://localhost/order.php", data=json.dumps(content))
			response = r.json()
			if response.get("Status") == 0:
				print("Turn on the lights!" + location)
				speech = "I have turned on the lights in the " + location + " !"
			elif response.get("Status") == 2:
				speech = "Oh, it seems your are not registered yet. Do you want to register right now?"
				res["contextOut"] = [{"name":"register", "lifespan":2}]
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
