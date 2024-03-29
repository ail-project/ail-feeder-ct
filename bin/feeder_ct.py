#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import base64
import configparser
import os
import re
import sys
import json
import math
import redis
import shutil
import signal
import pathlib
import dns.resolver

from M2Crypto import X509
from bs4 import BeautifulSoup

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from ail_typo_squatting import runAll

from pyail import PyAIL

pathProg = pathlib.Path(__file__).parent.absolute()

pathWork = ""
for i in re.split(r"/|\\", str(pathProg))[:-1]:
    pathWork += i + "/"


## Config
pathConf = '../etc/ail-feeder-ct.cfg'

if os.path.isfile(pathConf):
    config = configparser.ConfigParser()
    config.read(pathConf)
else:
    print("[-] No conf file found")
    exit(-1)

if 'general' in config:
    uuid = config['general']['uuid']
else:
    uuid = '1b43a925-a58e-4716-897f-bbbb9eb3ea9a'

if 'ail' in config:
    ail_url = config['ail']['url']
    ail_key = config['ail']['apikey']

if 'redis' in config:
    red = redis.Redis(host=config['redis']['host'], port=config['redis']['port'], charset="utf-8", decode_responses=True)
else:
    red = redis.Redis(host='localhost', port=6379, charset="utf-8", decode_responses=True)

if 'virustotal' in config:
    vt_key = config['virustotal']['apikey']
else:
    vt_key = None

sub = red.pubsub()
sub.subscribe('ct-certs', ignore_subscribe_messages=False)


# RR
type_request = ['UNSPEC', 'MF', 'NSEC3PARAM', 'EUI64', 'NS', 'SPF', 'NSAP-PTR', 'MG', 'APL', 'TSIG', 'DS', 'TLSA', 'HIP', 'MINFO', 'CSYNC', 'ANY', 'RRSIG', 'CDS', 'NSAP', 'CAA', 'A', 'URI', 'A6', 'KEY', 'KX', 'EUI48', 'SSHFP', 'MAILA', 'RT', 'WKS', 'DLV', 'DNAME', 'PX', 'DHCID', 'MD', 'NULL', 'TA', 'SIG', 'NSEC3', 'MR', 'AXFR', 'CDNSKEY', 'NONE', 'MB', 'TKEY', 'RP', 'NXT', 'SRV', 'SOA', 'MX', 'GPOS', 'AFSDB', 'NAPTR', 'DNSKEY', 'TXT', 'HINFO', 'NSEC', 'IPSECKEY', 'CERT', 'X25', 'PTR', 'MAILB', 'CNAME', 'ISDN', 'AAAA', 'LOC', 'IXFR', 'OPT']

def signal_handler(sig, frame):
    """Ctrl + c"""
    sys.exit(0)


def jsonCreation(all_domains, domainMatching, variationMatching, certificat, dns_resolve, website_dict, vt_result):
    """Json Creation"""
    json_output = dict()
    json_output["certificat"] = certificat
    json_output["domains"] = all_domains
    json_output["domain_matching"] = domainMatching
    json_output["variation_matching"] = variationMatching

    if dns_resolve:
        json_output["dns_resolve"] = dns_resolve

    if website_dict:
        json_output["website_info"] = website_dict

    if vt_result:
        json_output["virus_total"] = vt_result

    with open(os.path.join(pathOutput, domainMatching), "w") as write_file:
        json.dump(json_output, write_file)


def webSiteTitleGrab(domain):
    """Grab title of the web site if it's possible"""

    website_dict = dict()

    try:
        url = f"https://{domain}"
        response = requests.get(url, verify=False)

        website_dict["url"] = url
        website_dict["headers"] = dict(response.headers)

        if response.history:
            website_dict["redirect"] = len(response.history)

        if "200" in str(response):
            soup = BeautifulSoup(response.content, "html.parser")
            title = soup.find_all('title', limit=1)
            if title:
                t = str(title[0])
                t = t[7:]
                t = t[:-8]
                website_dict["website_title"] = t
    except:
        pass

    return website_dict

def virusTotal(domain):
    """Check domain on virus total"""

    api_url = f'https://www.virustotal.com/api/v3/domains/{domain}'
    headers = {'x-apikey' : vt_key}

    try:
        response = requests.get(api_url, headers=headers)
    except requests.exceptions.ConnectionError:
        return None

    if response.status_code == 200:
        return response.json()
    return None


def dnsResolver(domain, domain_matching, warning, verbose, pyail):
    """DNS actions"""

    domain_resolve = dict()

    resolver = dns.resolver.Resolver()
    resolver.timeout = 0.2
    resolver.lifetime = 0.2

    for t in type_request:
        try:
            answer = resolver.resolve(domain, t)
            loc = list()
            for rdata in answer:
                loc.append(rdata.to_text())

            if warning:
                if t == 'CNAME':
                    for element in loc:
                        if not element.endswith(domain_matching + '.'):
                            if pyail:
                                meta_dict = {}
                                meta_dict["ct:domain_matching"] = domain_matching
                                meta_dict["ct:domain_catch"] = domain
                                meta_dict["ct:cname_alert"] = True
                                source = 'feeder-ct'
                                source_uuid = uuid
                                pyail.feed_json_item(f"europa.eu\n {element}", meta_dict, source, source_uuid, 'utf-8')
                            if verbose:
                                print("******************************************************************")
                                print(f"** CNAME: \'{element}\' **")
                                print("** Doesn't contain any of initial domains: **")
                                print(f"** {domain_matching} **")
                                print("******************************************************************")

            domain_resolve[t] = loc
        except:
            pass

    return domain_resolve


def domainFind(domain, dm, m, all_domains, vt, warning, verbose, pyail):
    dns_resolve = dict()
    if verbose:
        print("\n!!! FIND A DOMAIN !!!")
        d = domain.rstrip('\n')
        print(f"{d} matching with {dm}")

    dns_resolve = dnsResolver(domain, dm, warning, verbose, pyail)
    website = webSiteTitleGrab(domain)
    if pyail:
        pyail.crawl_url(domain, har=True, screenshot=True)
    vt_result = None
    if vt:
        vt_result = virusTotal(domain)
    jsonCreation(all_domains, domain, dm, m['data'].rstrip(), dns_resolve, website, vt_result)


def get_ct(vt, matching_string, warning, verbose, pyail):
    """Core function"""
    global sub, red

    signal.signal(signal.SIGINT, signal_handler)

    try:
        m = sub.get_message()
    except:
        if 'redis' in config:
            red = redis.Redis(host=config['redis']['host'], port=config['redis']['port'], charset="utf-8", decode_responses=True)
        else:
            red = redis.Redis(host='localhost', port=6379, charset="utf-8", decode_responses=True)
        sub = red.pubsub()
        sub.subscribe('ct-certs', ignore_subscribe_messages=False)
        m = sub.get_message()

    if m:
        if type(m['data']) is not int:
            cert_der = base64.b64decode(m['data'].rstrip())

            x509 = X509.load_cert_string(cert_der, X509.FORMAT_DER)

            # Subject domain name
            try:
                subject = x509.get_subject().as_text()
                subject = subject.replace("CN=", "")
                # subject contain C, ST, O ...
                subject = subject.split(" ")[-1]
            except:
                subject = ""

            # Alternative domain name
            try:
                cAltName = x509.get_ext('subjectAltName').get_value()
                cAltName = cAltName.replace("DNS:", "").split(", ")
            except LookupError:
                cAltName = ""

            all_domains = list()
            if subject:
                all_domains.append(subject)
            if cAltName:
                for aName in cAltName:
                    all_domains.append(aName)

            for domain in all_domains:
                domain = deleteHead(domain)
                for dm in resultList:
                    # If ms option if choose
                    if matching_string:
                        if dm in domain:
                            domainFind(domain, dm, m, all_domains, vt, warning, verbose, pyail)
                            break

                    elif len(domain.split(".")) >= len(dm.split(".")):
                        # Reduce the length of domain name to match the length of variations
                        # Here, just the end is important
                        reduceDm = domain.split(".")
                        while len(reduceDm) > len(dm.split(".")):
                            reduceDm = reduceDm[1:]
                        reduceDm[-1] = reduceDm[-1].rstrip("\n")

                        if reduceDm == dm.split("."):
                            domainFind(domain, dm, m, all_domains, vt, warning, verbose, pyail)
                            break



def deleteHead(domain):
    """If domains begins with *, delete the 2 first caracters"""
    if domain.split(".")[0] == "*":
        locDomain = ""
        for element in domain.split(".")[1:]:
            locDomain += element + "."

        locDomain = locDomain[:-1].rstrip("\n")
        return locDomain

    return domain




if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-dn", "--domainName", nargs="+", help="list of domain name")
    parser.add_argument("-fdn", "--filedomainName", help="file containing list of domain name")

    parser.add_argument("-a", "--ail", help="Send domain to AIL crawler", action="store_true")
    parser.add_argument("-ats", "--ail_typo_squatting", help="Generate Variations for list pass in entry", action="store_true")
    parser.add_argument("-ms", "--matching_string", help="Match domain name if variations are in the domain name in any position", action="store_true")
    parser.add_argument("-vt", "--virustotal", help="Check domain on virus total", action="store_true")
    parser.add_argument("-w", "--warning", help="If CNAME is not the same as the matching domain then send a warning to AIL or just display a message", action="store_true")

    parser.add_argument("-o", "--output", help="path to ouput location, default: ../output")
    parser.add_argument("-v", "--verbose", help="verbose, more display", action="store_true")

    args = parser.parse_args()

    if not args.domainName or args.filedomainName:
        parser.print_help()
        sys.exit(0)

    domainList = list()

    matching_string = args.matching_string
    verbose = args.verbose
    vt = args.virustotal
    warning = args.warning

    # Path for json output
    pathOutput = args.output
    if not pathOutput:
        pathOutput = os.path.join(pathWork, "output")
        if not os.path.isdir(pathOutput):
            os.mkdir(pathOutput)

    # Domain name to process
    if args.filedomainName:
        with open(args.filedomainName, "r") as read_file:
            for lines in read_file.readlines():
                domainList.append(lines.rstrip("\n"))
    elif args.domainName:
        domainList = args.domainName
    else:
        print("[-] No domain name given")
        exit(-1)

    if args.ail:
        try:
            pyail = PyAIL(ail_url, ail_key, ssl=False)
        except Exception as e:
            print('[ERROR] Unable to connect to AIL Framework API. Please check [AIL] url, apikey and verifycert in '
                  '../etc/conf.cfg.\n')
            sys.exit(0)
    else:
        pyail = False



    resultList = list()

    # Generation of variations
    if args.ail_typo_squatting:
        pathTrash = os.path.join(pathWork, "trash")
        if not os.path.isdir(pathTrash):
            os.mkdir(pathTrash)

        for domain in domainList:
            print(f"\n **** Variations Generations for {domain} ****")
            resultList = runAll(domain, math.inf, formatoutput="text", pathOutput=pathTrash, verbose=verbose)

        shutil.rmtree(pathTrash)
    else:
        resultList = domainList

    # Call of the core function
    while True:
        get_ct(vt, matching_string, warning, verbose, pyail)
