# collectd-cloudstack - cloudstack.py
#
# Author : Antoine Coetsier @ exoscale
# Description : This is a collectd python module to gather stats from cloudstack
# inspired by collectd-haproxy from Michael Leinartas - https://github.com/mleinart/collectd-haproxy

import collectd
import urllib2
import urllib
import json
import hmac
import base64
import hashlib
import re
import lib/CloudStack

NAME = 'cloudstack'

DEFAULT_API = 'http://localhost:8096/client/api'
DEFAULT_AUTH = False
DEFAULT_APIKEY = ''
DEFAULT_SECRET = ''
VERBOSE_LOGGING = False

METRIC_TYPES = {
  'hmemused': ('host_memory_used', 'bytes'),
  'hmemtotal': ('host_memory_total', 'bytes'),
  'hmemalloc': ('host_memory_allocated', 'bytes')
}

METRIC_DELIM = '.'

hypervisors = []

def get_stats():
  stats = dict()
  
  logger('verb', "get_stats calls API %s KEY %s SECRET %s" % (API_MONITORS, APIKEY_MONITORS, SECRET_MONITORS))
  cloudstack = CloudStack.Client(API_MONITORS, APIKEY_MONITORS, SECRET_MONITORS)	
  try:
 	hypervisors = cloudstack.listHosts({
                        'type': 'Routing'
                }) 
  except:
     	logger('warn', "status err Unable to connect to CloudStack URL at %s" % API_MONITORS)
  for  host in cloudstack.hosts_stats():
	metricname = METRIC_DELIM.join([ host['name'].lower(), host['podname'].lower(), 'memoryused' ])
	try:
        	stats[metricname] = host['memoryused'] 
	except (TypeError, ValueError), e:
        	pass
	return stats	



# callback configuration for module
def configure_callback(conf):
  global API_MONITORS, APIKEY_MONITORS, SECRET_MONITORS, AUTH_MONITORS, VERBOSE_LOGGING
  API_MONITORS = '' 
  APIKEY_MONITORS = ''
  SECRET_MONITORS = ''
  AUTH_MONITORS = DEFAULT_AUTH
  VERBOSE_LOGGING = False

  for node in conf.children:
    if node.key == "Api":
      API_MONITORS = node.values[0]
    elif node.key == "ApiKey":
      APIKEY_MONITORS = node.values[0]
    elif node.key == "Secret":
      SECRET_MONITORS = node.values[0]
    elif node.key == "Auth":
      AUTH_MONITORS = node.values[0]
    elif node.key == "Verbose":
      VERBOSE_LOGGING = bool(node.values[0])
    else:
      logger('warn', 'Unknown config key: %s' % node.key)

  if not API_MONITORS:
    API_MONITORS += DEFAULT_API

def read_callback():
  logger('verb', "beginning read_callback")
  info = get_stats()

  if not info:
    logger('warn', "%s: No data received" % NAME)
    return

  for key,value in info.items():
    key_prefix = ''
    key_root = key
    if not value in METRIC_TYPES:
      try:
        key_prefix, key_root = key.rsplit(METRIC_DELIM,1)
      except ValueError, e:
        pass
    if not key_root in METRIC_TYPES:
      continue

    key_root, val_type = METRIC_TYPES[key_root]
    key_name = METRIC_DELIM.join([key_prefix, key_root])
    val = collectd.Values(plugin=NAME, type=val_type)
    val.type_instance = key_name
    val.values = [ value ]
    val.dispatch()


# logging function
def logger(t, msg):
    if t == 'err':
        collectd.error('%s: %s' % (NAME, msg))
    elif t == 'warn':
        collectd.warning('%s: %s' % (NAME, msg))
    elif t == 'verb':
        if VERBOSE_LOGGING:
            collectd.info('%s: %s' % (NAME, msg))
    else:
        collectd.notice('%s: %s' % (NAME, msg))
# main
collectd.register_config(configure_callback)
collectd.register_read(read_callback)
