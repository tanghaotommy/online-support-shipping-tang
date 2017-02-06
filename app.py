#!/usr/bin/env python
#coding:utf-8
import urllib
import json
import os
import requests
import sys
reload(sys)
sys.setdefaultencoding( "utf-8" )

from flask import Flask
from flask import request
from flask import make_response

import logging

import mysql.connector
#from mysql.connector import errorcode

mysql_config = config = {
  'user': 'root',
  'password': 'password',
  'host': 'mysql.cii5tvbuf3ji.us-west-1.rds.amazonaws.com',
  'database': 'RestaurantsRecommendation'
}

class Mysql(object):

	def connect(self, config):
		try:
		  self.cnx = mysql.connector.connect(**config)
		  return None
		except err:
			print err
			self.cnx = None
			return err
		else:
		  self.cnx.close()
		  self.cnx = None
		  return 0

	def close(self):
		if self.cnx: self.cnx.close(); self.cnx=None;

	def query(self, query,schema=None):
		cursor = self.cnx.cursor()

		cursor.execute(query)
		result = []
		for i, row in enumerate(cursor):
			if schema == None:
				result.append(row)
			else:
				dict = {}
				for j, column in enumerate(row):
					print j
					print column
					if j >= len(schema):
						break
					if isinstance(column, unicode):
						dict[schema[j]] = column.encode('utf-8')
					else:
						dict[schema[j]] = column
				result.append(dict)
		print result
		# for (first_name, last_name, hire_date) in cursor:
		#   print("{}, {} was hired on {:%d %b %Y}".format(
		#     last_name, first_name, hire_date))

		cursor.close()
		return result
	def __del__(self):
		if self.cnx: self.cnx.close(); self.cnx=None;


# Flask app should start in global layout
app = Flask(__name__)
print ('嘿嘿')

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

@app.route('/restaurantsRec', methods=['POST'])
def restaurantsRec():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = makeResponse2(req)

    res = json.dumps(res, indent=4)
    print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def makeResponse2(req):
	action = req.get("result").get("action")
	result = req.get("result")
	facebook_userId = str(req.get("sessionId"))
	parameters = result.get("parameters")
	res = {}
	speech = '出错啦！！！'
	if action == 'query.restaurants':
		speech = "你喜欢什么类型的菜？"
	if action == 'query.restaurants.location':
		speech = "能把你的位置发送给我嘛？"
	if action == 'query.restaurants.taste':
		speech = "正在寻找中，请稍等！"
	if action == 'query.restaurants.unknownLocation':
		mysql = Mysql()
		if(mysql.connect(mysql_config) == None):
			speech = 'Success'
			schema = ['id', 'name_en', 'name_cn', 'rating', 'type']
			results = mysql.query("SELECT * FROM Restaurants", schema)
			mysql.close()
			speech = "我们给你推荐" + results[0]['name_cn']
		else:
			speech = 'Database Error'

		#speech = result.get('resolvedQuery')

	print("Response:" + str(speech))
	res["speech"] = speech
	res["displayText"] = speech
	res["source"] = "shokse-restaurants-recommendation"

	return res;


def makeResponse(req):
	action = req.get("result").get("action")
	result = req.get("result")
	facebook_userId = str(req.get("sessionId"))
	parameters = result.get("parameters")
	res = {}

	if action == "action.uploadphoto":
		print("Add face picture to training set!")
		content = {
			"Type": "AddFace",
			"Id": facebook_userId
		}
		print content
		r = requests.post("http://localhost/order.php", data=json.dumps(content))
		response = r.json()
		print response
		if response.get("Status") == 0:
			speech = "I have added this photo to the database. Our facial recognition is more precise ever before!"
		else:
			speech = "Sorry, I meet some errors. Please try again later!"

	if action == "action.register":
		print("New user registers!")
		content = {
			"Type": "register",
			"Id": facebook_userId
		}
		print content
		r = requests.post("http://localhost/register.php", data=json.dumps(content))
		response = r.json()
		print response
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
			speech = "Sure! Wait a moment, picture is on its way!"
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

    # logging.basicConfig(level=logging.DEBUG,
    #             format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    #             datefmt='%a, %d %b %Y %H:%M:%S',
    #             filename='app.log',
    #             filemode='w')
    # logging.debug('This is debug message')
    # logging.info('This is info message')
    # logging.warning('This is warning message')

    print "Starting app on port %d" % port

    app.run(debug=False, port=port, host='0.0.0.0')
