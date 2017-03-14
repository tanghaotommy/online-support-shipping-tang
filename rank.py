import numpy as np
import config
def rank(restaurants, method = "distance", submethod = "overall", pivot = None, reverse = False, reverse_sub = True):
	#restaurants: a maps of id to attributes of the restaurants
	#method: the method to sort the restaurants
	#submethod: the method to sort the two lists splitted by pivot, only used when pivot is note None
	#pivot: the id of the restaurants, from which to be splitted
	#reverse: whether reverse the rank
	#reverse_sub: whether to reverse the rank of sub lists

	#Note: the submethod, reverse_sub is used if and only if pivot is not None.
	if not pivot:
		return _rank(restaurants, method = method, reverse = reverse)
	else:
		if method == "distance":
			return _splitAndRank(restaurants, method = method, submethod = submethod, pivot = pivot, reverse = False, reverse_sub = reverse_sub)
		if method == "price_averge":
			return _splitAndRank(restaurants, method = method, submethod = submethod, pivot = pivot, reverse = False, reverse_sub = reverse_sub)
		if method == "rating":
			return _splitAndRank(restaurants, method = method, submethod = submethod, pivot = pivot, reverse = True, reverse_sub = reverse_sub)

def _splitAndRank(restaurants, method, submethod, pivot, reverse, reverse_sub):
	value = restaurants[pivot][method]
	leftList = []
	rightList = []
	for restaurant_id, attr in restaurants.iteritems():
		if attr[method] < value:
			leftList.append(restaurant_id)
		else:
			rightList.append(restaurant_id)
	# print leftList
	# print rightList
	if reverse: 
		return _rank(restaurants, method = submethod, reverse = reverse_sub, array = rightList) + (_rank(restaurants, method = submethod, reverse = reverse_sub, array = leftList))
	else:
		return _rank(restaurants, method = submethod, reverse = reverse_sub, array = leftList) + (_rank(restaurants, method = submethod, reverse = reverse_sub, array = rightList))

def _rank(restaurants, method, reverse, array = None):
	if not array:
		return sorted(restaurants, key = lambda restaurant: restaurants[restaurant][method], reverse = reverse)
	else:
		return sorted(array, key = lambda restaurant: restaurants[restaurant][method], reverse = reverse)

def calculateOverallScore(restaurants):
	distance = []
	rating = []
	price_average = []
	for restaurant_id, attr in restaurants.iteritems():
		distance.append(attr["distance"])
		rating.append(attr["rating"])
		price_average.append(np.mean([int(x) for x in attr["price_average"].split("-")]))
	# print distance
	# print rating
	# print price_average
	# for i, t in enumerate(restaurants.iteritems()):
	# 	t[1]["overall"] = distance[i] + rating[i] + price_average[i]
	# print restaurants
	# print price_average
	weights = [config.weights["distance"], config.weights["rating"], config.weights["price_average"]]
	m = np.array((distance, rating, price_average))
	score = m.T.dot(np.array((weights)))
	# print m
	# print score
	for i, t in enumerate(restaurants.iteritems()):
		t[1]["overall"] = score[i]
	return restaurants
	# print restaurants


if __name__ == '__main__':
	restaurants = {3: {"distance": 14.3, "rating": 3.8, "overall": 0.8, "price_average": "10-20"},
				4: {"distance": 15.8, "rating": 5.0, "overall": 0.5, "price_average": "10"},
				5: {"distance": 7.2, "rating": 4.0, "overall": 0.9, "price_average": "20"},
				6: {"distance": 2.3, "rating": 4.5, "overall": 0.3, "price_average": "30"},
				7: {"distance": 5.2, "rating": 3.0, "overall": 0.6, "price_average": "40"}}

	sorted_key_list = sorted(restaurants, key=lambda restaurant: restaurants[restaurant]["rating"])
	print sorted_key_list
	for i in sorted_key_list:
		print restaurants[i]
	sorted_key_list = sorted(restaurants, key=lambda restaurant: restaurants[restaurant]["distance"])
	print sorted_key_list
	for i in sorted_key_list:
		print restaurants[i]
	print "Rank by distance splitted by distance: ", rank(restaurants, method = "distance", submethod = "distance", reverse = False, reverse_sub = False, pivot = 5)
	print "Default: ", rank(restaurants)
	print "Rank by overall score: ", rank(restaurants, method = "overall", reverse = True)
	print "Rank by rating: ", rank(restaurants, method = "rating", reverse = True)
	print "Rank by overall score splitted by distance: ", rank(restaurants, method = "distance", reverse = False, reverse_sub = True, pivot = 5)
	print calculateOverallScore(restaurants)