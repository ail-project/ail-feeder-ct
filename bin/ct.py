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
## Redis Config
if 'redis' in config:
    r = redis.Redis(host=config['redis']['host'], port=config['redis']['port'], db=config['redis']['db'])
else:
    r = redis.Redis(host='localhost', port=6379, db=0)
    
## CertStream URL config
if len(config['certstream']['url']) >= 1:
    certstreamUrl = config['certstream']['url']
    print("Using Config file CertStream server:")
    print(certstreamUrl)
else:
    certstreamUrl = 'wss://certstream.calidog.io/full-stream' # <--This stream is publicly available
    print("Using fallback CertStream:")
    print(certstreamUrl)

## CertStream data retrieval
def print_callback(message, context):

    if message['message_type'] == "heartbeat":
        return

    if message['message_type'] == "certificate_update":
        all_domains = message['data']['leaf_cert']['all_domains']


        if len(all_domains) != 0:

            sys.stdout.write(u"[{}] {} (SAN: {})\n".format(datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S'), all_domains[0], ", ".join(all_domains[1:])))

            cert_der = str(message['data']['leaf_cert']['as_der'])
            r.publish('ct-certs', u"{}\n".format(cert_der))

            sys.stdout.flush()


certstream.listen_for_events(print_callback, url=certstreamUrl)
