#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import datetime
import certstream
import redis
import configparser

## Config
pathConf = '../etc/ail-feeder-ct.cfg'

if os.path.isfile(pathConf):
    config = configparser.ConfigParser()
    config.read(pathConf)
else:
    print("[-] No conf file found")
    exit(-1)

if 'cache' in config:
    cache_expire = config['cache']['expire']
else:
    cache_expire = 86400

if 'redis' in config:
    r = redis.Redis(host=config['redis']['host'], port=config['redis']['port'], db=config['redis']['db'])
else:
    r = redis.Redis(host='localhost', port=6379, db=0)


def print_callback(message, context):

    if message['message_type'] == "heartbeat":
        return

    if message['message_type'] == "certificate_update":
        all_domains = message['data']['leaf_cert']['all_domains']


        if len(all_domains) != 0:

            """sys.stdout.write(u"[{}] {} (SAN: {})\n".format(datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S'), all_domains[0], ", ".join(all_domains[1:])))
       
            r.publish('ct-certs', u"{}\n".format(all_domains))
        sys.stdout.flush()"""

            sys.stdout.write(u"[{}] {} (SAN: {})\n".format(datetime.datetime.now().strftime('%m/%d/%y %H:%M:%S'), all_domains[0], ", ".join(all_domains[1:])))
            cert_der = str(message['data']['leaf_cert']['as_der'])
            r.publish('ct-certs', u"{}\n".format(cert_der))
            sys.stdout.flush()
        

certstream.listen_for_events(print_callback, url='ws://crd.circl.lu:4000/full-stream')
