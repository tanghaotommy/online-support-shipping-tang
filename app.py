#!/usr/bin/env python
#coding:utf-8
import urllib
import json
import os
import requests
import re
import time
import copy
import sys
from pymongo import MongoClient
import math
reload(sys)
sys.setdefaultencoding( "utf-8" )

import random
from flask import Flask
from flask import request
from flask import make_response
import config
import rank

import logging
import mysql.connector
#from mysql.connector import errorcode

MAXNUMBEROFRESTAURANTS = 100
MAXDISTANCE = 300
GOOGLEMAPS_API_KEY = "AIzaSyABcAARrYGpUs-9PCD1B7tdl3tMaxGHBZU"
mysql_config = {
  'user': 'root',
  'password': 'password',
  'host': 'newdatabase.cii5tvbuf3ji.us-west-1.rds.amazonaws.com',
  'database': 'RestaurantsRecommendation'
}
restaurant_schema = ['id', 'name_en', 'name_cn', 'rating', 'type', 'signature', 'price_average', 'address', 'phone', 
'hour', 'city', 'state', 'zip', 'website', 'latitude', 'longitude']
waitingtime_schema = ["restaurant_id", "waiting_time"]
flavor_taste = {
	'辣的': '川菜',
	'甜的': '上海菜'
}

answers_query_restaurants = ['Hello客官你来啦(づ￣3￣)づ╭❤～\n今天想试一试哪种风格的美食呢？']

answers_query_restaurants_location = ['好的，请稍等！正在搜寻中！']

answers_query_restaurants_taste = ['%s是个很棒的选择哦[CoolGuy][CoolGuy]。那你能告诉我你的位置么？这\
样我好帮你寻找符合条件的餐馆。你可以直接打你所在的地址，也可以发送你当前位置。（可以在公众号设置内允许我访问你的当前位置，这样以后就不用你输入地址啦！）',
'%s是个很棒的选择哦[CoolGuy][CoolGuy]。\n好的宝贝~我已经检测到你当前的地址啦O(∩_∩)O~，可以直接使用它进行查找嘛？[Laugh][Laugh][Laugh]\n或者你也可以输入其他地址哦！']

answers_query_restaurants_unknownLocation = ['请问是%s嘛？~', '对不起，我不知道这个是哪里。你能再说一遍么？']

answers_query_restaurants_withoutTaste = ['好的哟～我有搜索到您附近好评最高的餐厅。\n那你能告诉我你的位置么？这\
样我好帮你寻找符合条件的餐馆。你可以直接打你所在的地址，也可以发送你当前位置。（可以在公众号设置内允许我访问你的当前位置，这样以后就不用你输入地址啦！）',
'好的哟～我有搜索到您附近好评最高的餐厅。\n好的宝贝~我已经检测到你当前的地址啦O(∩_∩)O~，可以直接使用它进行查找嘛？或者你也可以输入其他地址哦！']

answers_query_taste = ['你是想让我给你推荐%s嘛？', '你是想吃%s嘛？']

answers_query_restaurants_closer = ['这家叫%s（%s）的稍微近一些。招牌菜是%s。\n距离您现在的位置%s有%skm。%s\n营业时间是%s哦！\n你喜欢嘛?', 
'对不起啊，我找不到更近的餐馆了。最近的就是这家叫%s（%s）的。招牌菜是%s。\n距离您现在的位置%s有%skm。%s\n营业时间是%s哦！\n你喜欢嘛？[Rose][Rose][Rose]']

answers_query_restaurants_show = ['我觉得%s（%s）很好哦。招牌菜是%s。\n距离您现在的位置%s有%skm。%s\n营业时间是%s哦！\n不知道您对这家可还中意呀?[Rose][Rose][Rose]']

answers_query_restaurants_moreInformation = ["哈哈~您喜欢就太棒啦！这家餐厅的地址是%s。\n联系电话是%s\nBTW, 悄悄说一句，这家餐厅人均消费是$%s左右～\n那我这次的推荐就结束啦~温馨小提示，记得照顾好同行的小伙伴，酒后不要开车。祝您出行安全、用餐愉快哦O(∩_∩)O[Chuckle][Chuckle][Chuckle]"]

answers_query_restaurants_next = ['好嘞！我马上给您换另一家！\n' + answers_query_restaurants_show[0], "我找不到更多的餐厅啦，只能从头再开始一遍咯！\n" + answers_query_restaurants_show[0]]

piece_answer_waitingtime = ["\n目前预测的等待时间大概是%s分钟哦！"]

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
					#print j
					#print column
					if j >= len(schema):
						break
					if isinstance(column, unicode):
						dict[schema[j]] = column.encode('utf-8')
					else:
						dict[schema[j]] = column
				result.append(dict)
		#print result
		# for (first_name, last_name, hire_date) in cursor:
		#   print("{}, {} was hired on {:%d %b %Y}".format(
		#     last_name, first_name, hire_date))

		cursor.close()
		return result
	def __del__(self):
		if self.cnx: self.cnx.close(); self.cnx=None;


# Flask app should start in global layout
app = Flask(__name__)

@app.route('/user_location', methods=['POST'])
def user_location():
	req = request.get_json(silent=True, force=True)

	print("Request received from WeChat to in user_location.")
	#print(json.dumps(req, indent=4))

	res = "Success"

	client = MongoClient()
	db = client.wechat

	if db.UserLocation.find({"user_id": req['user_id']}).count() >= 1:
		#db.UserLocation.update({"user_id": req['user_id']}, {"user_id": req['user_id'], "timestamp": time.time(), "location": {"latitude": req['latitude'], "longitude": req['longitude']}})
		db.UserLocation.update({"user_id": req['user_id']}, {"$set": {"timestamp": time.time(), "location": {"latitude": req['latitude'], "longitude": req['longitude']}}})
		print "Update location of user: %s!" % (req['user_id'])
	else:
		db.UserLocation.insert_one({"user_id": req['user_id'], "timestamp": time.time(), "location": {"latitude": req['latitude'], "longitude": req['longitude']}})
		print "Insert location of user: %s!" % (req['user_id'])
	client.close()
	# user_location = db.UserLocation.find({"user_id": req['user_id']},{"_id": False})[0]
	# print user_location

	res = json.dumps(res, indent=4)
	print "Response: ", res 
	r = make_response(res)
	r.headers['Content-Type'] = 'application/json'
	return r

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

@app.route('/check_location', methods=['POST'])
def check_location():
   
    req = request.get_json(silent=True, force=True)
    print("Request received from WeChat in check_location.")
    print(json.dumps(req, indent=4))

    res = googleGeocode(req)

    res = json.dumps(res, indent=4)
    print "Response: ", res
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

@app.route('/restaurantsRec', methods=['POST'])
def restaurantsRec():
    req = request.get_json(silent=True, force=True)

    print("Request received from Api.ai in restaurantsRec")
    #print(json.dumps(req, indent=4))

    res = makeResponse2(req)
    res = json.dumps(res, indent=4)
 	#print(res)

    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def distance(LatA, LngA, LatB, LngB):
	#http://www.movable-type.co.uk/scripts/latlong.html
	phi1 = math.radians(LatA)
	phi2 = math.radians(LatB)
	deltaPhi = math.radians(LatB - LatA)
	deltaLambda = math.radians(LngB - LngA)

	a = math.sin(deltaPhi/2)*math.sin(deltaPhi/2) + math.cos(phi1)*math.cos(phi2)*math.sin(deltaLambda/2)*math.sin(deltaLambda/2)
	c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
	# C = math.sin(LatA)*math.sin(LatB)*math.cos(LngA-LngB) + math.cos(LatA)*math.cos(LatB)
	R = 6371.004
	# distance = round(R*math.acos(C)*math.pi/180, 1)
	distance = R * c
	return round(distance, 1)

def googleGeocode(req):
	latitude = req['latitude']
	longitude = req['longitude']
	address = str(latitude) + " " + str(longitude)
	address = re.sub(" ", '+', address)
	#print address
	url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s"
	url = url % (address, GOOGLEMAPS_API_KEY)
	r = requests.get(url)
	response = r.json()
	#print response
	res = {}
	if response['status'] == 'OK':
		formatted_address = response['results'][0]['formatted_address']
		speech = answers_query_restaurants_unknownLocation[0] % (formatted_address)
		res["contextOut"] = [{"name": "user_asks4_restaurants_withunknownlocation","parameters": {"location.original": address, "location": {'formatted_address': formatted_address,'location': response['results'][0]['geometry']['location']},},"lifespan": 3}]
	else:
		speech = answers_query_restaurants_unknownLocation[1]
	res["speech"] = speech
	res["displayText"] = speech
	res["source"] = "shokse-restaurants-recommendation"
	return res

def addToLog(user_id, data, action = "history"):
	if action == "history":
		client = MongoClient()
		db = client.wechat
		db.UserConfirmedHistory.insert_one({"user_id": user_id, "timestamp": time.time(), 
			"location": {"latitude": data["user_location"]["location"]["location"]["lat"], "longitude": data["user_location"]["location"]["location"]["lng"]}, 
			"taste": data["taste"], "dish": data["dish"], "flavor": data["flavor"],
			"total_recommendation": data["total"], "which": data["current"], "sorting_method": data["data"]["method"], "restaurant_id": data["lists"][data["current"]]
			})
		print "Added user's confirmation: %s!" % (user_id)
                client.close()

def clearContexts(contexts):
	for context in contexts:
		context["lifespan"] = 0
	return contexts

def deleteContext(contexts, name):
	for context in contexts:
		if context["name"] == name:
			context["lifespan"] = 0
			break
	return contexts

def extendContext(contexts, name, lifespan):
	for context in contexts:
		if context["name"] == name:
			context["lifespan"] = lifespan
			break
	return contexts

def findContext(contexts, name):
	for context in contexts:
		if context["name"] == name:
			return context
	return None

def getRestaurants(contexts, LatA, LngA, location_original = "", formatted_address = ""):
	contextOut = []
	parameters = findContext(contexts, "user_asks4_restaurants_withtaste")["parameters"]
	taste = parameters["taste"].encode('utf-8')
	if taste == '': taste = '-1'
	dish = parameters["dish"].encode('utf-8')
	if dish == '': dish = '-1'
	flavor = parameters["flavor"].encode('utf-8')
	print "taste: %s, " % (str(taste)), "dish: %s, " % (str(dish)), "flavor: %s" % (str(flavor))
	#print flavor_taste
	if flavor_taste.has_key(flavor):
		taste = flavor_taste[flavor]
	mysql = Mysql()
	if(mysql.connect(mysql_config) == None):
		if taste == "all":
			results = mysql.query("SELECT * FROM Restaurants", restaurant_schema)
		else:
			results = mysql.query("SELECT * FROM Restaurants WHERE type LIKE '%%%s%%' OR type LIKE '%%%s%%' OR signature LIKE '%%%s%%' OR signature LIKE '%%%s%%'" % (taste, dish, taste, dish), restaurant_schema)
		mysql.close()
		# print 'LatA' + str(LatA)
		# print 'LngA' + str(LngA)
		if len(results) > 0:
			restaurants = {}
			for i, row in enumerate(results):
				LatB = row['latitude']
				LngB = row['longitude']
				dist = distance(LatA, LngA, LatB, LngB)
				rating = row['rating']
				price_average = row['price_average']
				if dist <= MAXDISTANCE:
					restaurants[row['id']] = {"distance": dist, "rating": rating, "price_average": price_average, "overall": 1.0}

			restaurants = rank.calculateOverallScore(restaurants)
			sorted_key_list = rank.rank(restaurants, method = "overall", reverse = True)

			if len(sorted_key_list) >= 1:
				mysql.connect(mysql_config)
				item = mysql.query("SELECT * FROM Restaurants WHERE id=%d" % (sorted_key_list[0]), restaurant_schema)[0]
				mysql.close()

				user_location = {
					"location.original": location_original,
					"location": {
						"formatted_address": formatted_address,
						"location": {"lat": LatA, "lng": LngA}
						}
					}

				context = [{"name": "restaurants_recommended", "parameters": {
				"taste": parameters["taste"].encode('utf-8'),
				"dish": parameters["dish"].encode('utf-8'),
				"flavor": parameters["flavor"].encode('utf-8'),
				"lists": sorted_key_list,
				"max": len(sorted_key_list), 
				"batch_id": 1, 
				"current": 0,
				"total": len(results),
				"user_location": user_location,
				"data": {
					"method": "overall",
					"submethod": "",
					"reverse": True,
					"reverse_sub": False,
					"restaurants": restaurants}},
				"lifespan": 3}]
				contextOut = clearContexts(contexts)
				contextOut.extend(context)
				if formatted_address != "": 
					addr = "（%s）" % (formatted_address)
				else: 
					addr = ""
				# print sorted_key_list[0]
				# print 'LatB' + str(results[sorted_key_list[0]]['latitude'])
				# print 'LngB' + str(results[sorted_key_list[0]]['longitude'])
				# print str(distance(LatA, LngA, results[sorted_key_list[0]-1]['latitude'], results[sorted_key_list[0]]['longitude']))
				speech = generateRecommendationAnswer(sorted_key_list[0], user_location, answers_query_restaurants_show[0])
				# speech = answers_query_restaurants_show[0] % (item['name_cn'], item['name_en'], item['signature'],
				# 	addr, str(restaurants[sorted_key_list[0]]['distance']), item['hour'])
			else:
				contextOut = clearContexts(contexts)
				speech = "哎呀，对不起，在你附近我找不到符合条件的餐馆。"
		else:
			contextOut = clearContexts(contexts)
			speech = "哎呀，对不起，在你附近我找不到符合条件的餐馆。"
	else:
		speech = '哎呀！数据库出了点小问题！等我下！'
	return speech, contextOut

def generateRecommendationAnswer(restaurant_id, user_location, template):
	formatted_address = user_location["location"]["formatted_address"]
	if formatted_address != "": 
		addr = "（%s）" % (formatted_address)
	else:
		addr = ""
	mysql = Mysql()
	mysql.connect(mysql_config)
	item = mysql.query("SELECT * FROM Restaurants WHERE id=%d" % (restaurant_id), restaurant_schema)[0]
	mysql.close()

	LatA = item["latitude"]
	LngA = item["longitude"]
	LatB = float(user_location["location"]["location"]["lat"])
	LngB = float(user_location["location"]["location"]["lng"])

	waiting_time = getWaitingTime(restaurant_id)
	if not waiting_time == None:
		waiting_time = piece_answer_waitingtime[0] % (str(waiting_time))
	else:
		waiting_time = ""
	_distance = distance(LatA, LngA, LatB, LngB)
	speech = template % (item['name_cn'], item['name_en'], item['signature'], addr, str(_distance), waiting_time, item['hour'])
	return speech

def getWaitingTime(restaurant_id):
	mysql = Mysql()
	mysql.connect(mysql_config)
	items = mysql.query("SELECT * FROM WaitingTime WHERE restaurant_id=%d" % (restaurant_id), waitingtime_schema)
	mysql.close()
	if not items:
		return None
	else: 
		return items[0]["waiting_time"]

def makeResponse2(req):
	action = req.get("result").get("action")
	result = req.get("result")
	user_id = req.get("sessionId")
	parameters = result.get("parameters")
	res = {}
	print "Action: ", action
	speech = '出错啦！！！'

	if action == 'query.restaurants.closer':
		context = findContext(result["contexts"], "restaurants_recommended")
		lists = context["parameters"]["lists"]
		current = context["parameters"]["current"]
		user_location = context["parameters"]["user_location"]
		formatted_address = user_location["location"]["formatted_address"]
		if formatted_address != "": 
			addr = "（%s）" % (formatted_address)
		else:
			addr = ""
		if current > 0:
			current -= 1
			# mysql = Mysql()
			# mysql.connect(mysql_config)
			# item = mysql.query("SELECT * FROM Restaurants WHERE id=%d" % (lists[current]), restaurant_schema)[0]
			# mysql.close()

			# LatA = item["latitude"]
			# LngA = item["longitude"]
			# LatB = float(user_location["location"]["location"]["lat"])
			# LngB = float(user_location["location"]["location"]["lng"])

			# _distance = distance(LatA, LngA, LatB, LngB)
			# speech = answers_query_restaurants_closer[0] % (item['name_cn'], item['name_en'], item['signature'], addr, str(_distance), item['hour'])
			
			speech = generateRecommendationAnswer(lists[current], user_location, answers_query_restaurants_closer[0])
			context["parameters"]["current"] = current
			contextOut = [{"name": "restaurants_recommended", "parameters": context["parameters"], "lifespan": 3}]
			res["contextOut"] = clearContexts(result.get("contexts"))
			res["contextOut"].extend(contextOut)
		else:
			current = 0
			context["parameters"]["current"] = current
			contextOut = [{"name": "restaurants_recommended", "parameters": context["parameters"], "lifespan": 3}]
			res["contextOut"] = clearContexts(result.get("contexts"))
			res["contextOut"].extend(contextOut)

			# mysql = Mysql()
			# mysql.connect(mysql_config)
			# item = mysql.query("SELECT * FROM Restaurants WHERE id=%d" % (lists[current]), restaurant_schema)[0]
			# mysql.close()

			# LatA = item["latitude"]
			# LngA = item["longitude"]
			# LatB = float(user_location["location"]["location"]["lat"])
			# LngB = float(user_location["location"]["location"]["lng"])

			# _distance = distance(LatA, LngA, LatB, LngB)
			speech = generateRecommendationAnswer(lists[current], user_location, answers_query_restaurants_closer[1])
			# speech = answers_query_restaurants_closer[1] % (item['name_cn'], item['name_en'], item['signature'], addr, str(_distance), item['hour'])


	if action == 'query.taste':
		taste = parameters["taste"].encode('utf-8')
		dish = parameters["dish"].encode('utf-8')
		flavor = parameters["flavor"].encode('utf-8')
		speech = answers_query_taste[random.randint(0, len(answers_query_taste) - 1)] % (taste + dish + flavor)
		res['contextOut'] = clearContexts(result.get("contexts"))
		res['contextOut'] = extendContext(res['contextOut'], "user_mentions_taste", 3)


	if action == 'query.taste.positive':
		taste = findContext(result["contexts"], "user_mentions_taste")["parameters"]["taste"].encode('utf-8')
		dish = findContext(result["contexts"], "user_mentions_taste")["parameters"]["dish"].encode('utf-8')
		flavor = findContext(result["contexts"], "user_mentions_taste")["parameters"]["flavor"].encode('utf-8')
		client = MongoClient()
		contextOut = {"name": "user_asks4_restaurants_withTaste", 
		"parameters": {
			"taste": taste,
			"dish": dish,
			"flavor": flavor},
		"lifespan": 5}
		res["contextOut"] = clearContexts(result.get("contexts"))
		res["contextOut"].append(contextOut)
		db = client.wechat
		if db.UserLocation.find({"user_id": user_id}).count() >= 1:
			speech = answers_query_restaurants_taste[1] % (taste + dish + flavor)
		else:
			speech = answers_query_restaurants_taste[0] % (taste + dish + flavor)
		client.close()

	if action == 'query.restaurant':
		restaurant = parameters['restaurant_chinese']
		if not restaurant == "":
			mysql = Mysql()
			mysql.connect(mysql_config)
			print restaurant
			results = mysql.query("SELECT * FROM Restaurants WHERE name_en = '%s'" % (restaurant), restaurant_schema)
			if len(results) >= 1:
				item = results[random.randint(0, len(results) - 1)]
				href = "<a href='http://maps.apple.com/?q=%s,%s'>%s</a>" % (item["latitude"], item["longitude"], item["address"])
				speech = "你说的一定是%s（%s）。它在%s。他们家的招牌菜是%s。我说的对不对呀！" % (item['name_cn'], item['name_en'], href, item['signature'])
			else:
				speech = "哎呀，我不知道这是哪家店哎！过几天再来问问看呢。"
		else:
			speech = "你在说什么呀？"
			
	if action == 'query.restaurants':
		if result.has_key("contexts"): res["contextOut"] = clearContexts(result.get("contexts"))
		if not ((parameters["taste"] == "" and parameters["dish"] == "" and parameters["flavor"] == "")):
			client = MongoClient()
			db = client.wechat
			if db.UserLocation.find({"user_id": user_id}).count() >= 1:
				speech = answers_query_restaurants_taste[1] % (parameters.get('taste') + parameters.get('flavor') + parameters.get('dish'))
			else:
				speech = answers_query_restaurants_taste[0] % (parameters.get('taste') + parameters.get('flavor') + parameters.get('dish'))
			client.close()
			contextOut = [{"name": "user_asks4_restaurants_withtaste", "parameters": {
          "taste.original": "",
          "taste": parameters["taste"],
          "dish": parameters["dish"],
          "dish.original": "",
          "flavor": parameters["flavor"],
          "flavor.original": ""
        },
        "lifespan": 5}]
			if not (res["contextOut"] == ""):
				res["contextOut"].extend(contextOut)
			else:
				res["contextOut"] = {"contextOut": contextOut}
		else: 
			speech = answers_query_restaurants[random.randint(0, len(answers_query_restaurants) - 1)]
			contextOut = [{"name": "user_asks4_restaurantsrec", "parameters": {
			"taste.original": "",
			"taste": "",
			"dish": "",
			"dish.original": "",
			"flavor": "",
			"flavor.original": ""
			},
			"lifespan": 3}]
			if not (res["contextOut"] == ""):
				res["contextOut"].extend(contextOut)
			else:
				res["contextOut"] = {"contextOut": contextOut}
		#print '123'

	if action == 'delete.unknownLocation':
		speech = "Whoops~尴尬了~小客服学艺不精马上去面壁思过！宝宝能再告诉我一下你的详细地址吗？[Salute][Salute][Salute]"
		res["contextOut"] = deleteContext(result["contexts"], "user_asks4_restaurants_withunknownlocation")
		context = findContext(result["contexts"], "user_asks4_restaurants_withtaste")
		if context and context['lifespan'] <= 1:
			speech = "呜呜呜……为什么搞错那么多次，小客服今天要挨骂了/(ㄒoㄒ)/\n我还在长大，请给我一点时间学习❤ 再给我一次机会重来好不好\(^o^)/\n如果地址还是不对，宝宝也可以发地址给我，我在线帮您定位哦(⊙o⊙)[ThumbsUp][ThumbsUp][ThumbsUp]"
			res["contextOut"] = clearContexts(result.get("contexts"))

	if action == 'query.restaurants.location':
		client = MongoClient()
		db = client.wechat
		document = db.UserLocation.find({"user_id": user_id})[0]
		#print document
		location = document['location']
		#print location
		LatA = float(location['latitude'])
		LngA = float(location['longitude'])
		#print LatA
		#print LngA
		print "User %s is at: %s" % (str(user_id), str(location)) 
		client.close()
		speech, res['contextOut'] = getRestaurants(LatA=LatA, LngA=LngA, contexts=result.get("contexts"))

	if action == 'query.restaurants.taste':
		client = MongoClient()
		db = client.wechat
		if db.UserLocation.find({"user_id": user_id}).count() >= 1:
			speech = answers_query_restaurants_taste[1] % (parameters.get('taste') + parameters.get('dish') + parameters.get('flavor'))
		else:
			speech = answers_query_restaurants_taste[0] % (parameters.get('taste') + parameters.get('dish') + parameters.get('flavor'))
		client.close()

	if action == 'query.restaurants.unknownLocation':
		address = result.get('resolvedQuery')
		address = re.sub(" ", '+', address)
		url = "https://maps.googleapis.com/maps/api/geocode/json?address=%s&key=%s"
		url = url % (address, GOOGLEMAPS_API_KEY)
		r = requests.get(url)
		response = r.json()
		if response['status'] == 'OK':
			formatted_address = response['results'][0]['formatted_address']
			speech = answers_query_restaurants_unknownLocation[0] % (formatted_address)
			res["contextOut"] = [{"name": "user_asks4_restaurants_withunknownlocation","parameters": {"location.original": result.get('resolvedQuery'), "location": {'formatted_address': formatted_address,'location': response['results'][0]['geometry']['location']},},"lifespan": 3}]
		else:
			speech = answers_query_restaurants_unknownLocation[1]

	if action == 'query.restaurants.show':
		for context in result.get('contexts'):
			if context['name'] == 'user_asks4_restaurants_withunknownlocation':
				LatA = context['parameters']['location']['location']['lat']
				LngA = context['parameters']['location']['location']['lng']
				break
		speech, res['contextOut'] = getRestaurants(LatA=LatA, LngA=LngA, contexts=result.get("contexts"), 
			formatted_address=context['parameters']['location']['formatted_address'], 
			location_original=context['parameters']['location.original'])

	if action == 'query.restaurants.next':
		context = findContext(result["contexts"], "restaurants_recommended")
		lists = context["parameters"]["lists"]
		current = context["parameters"]["current"] + 1
		user_location = context["parameters"]["user_location"]
		formatted_address = user_location["location"]["formatted_address"]
		if formatted_address != "": 
			addr = "（%s）" % (formatted_address)
		else:
			addr = ""

		if current < context["parameters"]["max"] - 1:
			# mysql = Mysql()
			# mysql.connect(mysql_config)
			# item = mysql.query("SELECT * FROM Restaurants WHERE id=%d" % (lists[current]), restaurant_schema)[0]
			# mysql.close()

			# LatA = item["latitude"]
			# LngA = item["longitude"]
			# LatB = float(user_location["location"]["location"]["lat"])
			# LngB = float(user_location["location"]["location"]["lng"])

			# _distance = distance(LatA, LngA, LatB, LngB)
			# speech = answers_query_restaurants_next[0] % (item['name_cn'], item['name_en'], item['signature'], addr, str(_distance), item['hour'])
			speech = generateRecommendationAnswer(lists[current], user_location, answers_query_restaurants_next[0])
			context["parameters"]["current"] = current
			contextOut = [{"name": "restaurants_recommended", "parameters": context["parameters"], "lifespan": 3}]
			res["contextOut"] = clearContexts(result.get("contexts"))
			res["contextOut"].extend(contextOut)
		else:
			current = 0
			context["parameters"]["current"] = current
			contextOut = [{"name": "restaurants_recommended", "parameters": context["parameters"], "lifespan": 3}]
			res["contextOut"] = clearContexts(result.get("contexts"))
			res["contextOut"].extend(contextOut)

			# mysql = Mysql()
			# mysql.connect(mysql_config)
			# item = mysql.query("SELECT * FROM Restaurants WHERE id=%d" % (lists[current]), restaurant_schema)[0]
			# mysql.close()

			# LatA = item["latitude"]
			# LngA = item["longitude"]
			# LatB = float(user_location["location"]["location"]["lat"])
			# LngB = float(user_location["location"]["location"]["lng"])

			# _distance = distance(LatA, LngA, LatB, LngB)
			speech = generateRecommendationAnswer(lists[current], user_location, answers_query_restaurants_next[1])
			# speech = answers_query_restaurants_next[1] % (item['name_cn'], item['name_en'], item['signature'], addr, str(_distance), item['hour'])	

	if action == 'query.restaurants.moreInformation':
		context = findContext(result["contexts"], "restaurants_recommended")
		lists = context["parameters"]["lists"]
		current = context["parameters"]["current"]
		mysql = Mysql()
		mysql.connect(mysql_config)
		item = mysql.query("SELECT * FROM Restaurants WHERE id=%d" % (lists[current]), restaurant_schema)[0]
		mysql.close()

		addToLog(user_id, context["parameters"], action = "history")

		res["contextOut"] = clearContexts(result.get("contexts"))
		contextOut = [{"name": "restaurants_recommended_accepted", "parameters": {
		"current": current},
		"lifespan": 3}]
		res["contextOut"].extend(contextOut)

		href = "<a href='http://maps.apple.com/?q=%s,%s'>%s</a>" % (item["latitude"], item["longitude"], item["address"])
		speech = answers_query_restaurants_moreInformation[0] % (href, item["phone"], item["price_average"])
		#speech = result.get('resolvedQuery')

	if action == 'query.restaurants.withoutTaste':
		client = MongoClient()
		db = client.wechat
		if db.UserLocation.find({"user_id": user_id}).count() >= 1:
			speech = answers_query_restaurants_withoutTaste[1]
		else:
			speech = answers_query_restaurants_withoutTaste[0] 
		client.close()
                res["contextOut"] = clearContexts(result.get("contexts"))
		contextOut = [{"name": "user_asks4_restaurants_withtaste", "parameters": {
		"taste.original": "",
		"taste": "all",
		"dish": "",
		"dish.original": "",
		"flavor": "",
		"flavor.original": ""},
		"lifespan": 5}]
                res["contextOut"].extend(contextOut)

	if action == 'test':
		wechat = {
			"wechat": [{
    				"title": '我觉得这家不错，你喜欢嘛？',
    				"description": '<a href="http://54.183.198.179/UploadedFaceImages/1483855032.jpg">店面信息</a>',
    				"picurl": 'http://54.183.198.179/UploadedFaceImages/1483855032.jpg',
    				"url": 'http://nodeapi.cloudfoundry.com/'
  			}]
		}
		speech = '<a href="http://54.183.198.179/UploadedFaceImages/1483855032.jpg">店面信息</a>'
		#res["data"] = wechat
		speech = "<a href='http://maps.google.com/maps/?q=34.0800231,-118.1026794'>a place</a>"

	print("Response: " + str(speech))
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
