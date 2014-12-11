#!/usr/bin/env python
import json
import sys
import httplib
import time

# States
STATE_OK = 0
STATE_WARNING = 1
STATE_CRITICAL = 2
STATE_UNKNOWN = 3

# Status URI
STATUS_DOWN_URI = '/api/v1/statuses/1/'
STATUS_UP_URI = '/api/v1/statuses/2/'
STATUS_DOWN_NAME = 'Down'
STATUS_UP_NAME = 'Up'

HOSTNAME = '127.0.0.1'
PORT = '8910'

# Read info from Sensu handler
sensu_event = sys.stdin.read()
sensu_json = json.loads(sensu_event)

# Connect to the  Whiskerboard API
conn = httplib.HTTPConnection(HOSTNAME, PORT)

# Get service list
conn.request('GET', '/api/v1/services/')
response_service = conn.getresponse()
services_list = json.loads(response_service.read())

# Small function just to take care of basic_auth for POST requests
def basic_authorization(user, password):
	s = '%s:%s' % (user, password)
	return "Basic " + s.encode('base64').rstrip()

# Set headers for Authentication on POST requests
headers = {
	'Content-type': 'application/json',
	'Authorization': basic_authorization('user', 'password'),
	'Accept': '*/*',
	'User-Agent': 'Sensu handler',
}

for service in services_list['objects']:
        sensu_check_name = sensu_json['check'].get('name').lower()
	slug_name = service.get('slug').lower()
        if slug_name == sensu_check_name:
		if sensu_json['check'].get('status') == STATE_OK:
			params = {
				"status" : STATUS_UP_URI,
				"service" : service.get('resource_uri'),
				"start" : time.strftime("%Y-%m-%dT%H:%M:%S"),
        			"message" : "The service is up",
				"informational": False,
			}
		elif sensu_json['check'].get('status') == STATE_CRITICAL:
			if not service.get('current-event') or service.get('current-event')['status'] != STATUS_DOWN_NAME:
				params = {
					"status" : STATUS_DOWN_URI,
					"service" : service.get('resource_uri'),
					"start" : time.strftime("%Y-%m-%dT%H:%M:%S"),
	        			"message" : "The service is currently down",
					"informational": False,
				}

params = json.dumps(params)

conn.request('POST', '/api/v1/events/', params, headers)
response = conn.getresponse()
data = response.read()
