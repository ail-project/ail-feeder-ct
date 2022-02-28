import os
import re
import sys
import json
import redis
import base64
import pathlib
import argparse
import configparser
from M2Crypto import X509

pathProg = pathlib.Path(__file__).parent.absolute()

pathWork = ""
for i in re.split(r"/|\\", str(pathProg))[:-1]:
    pathWork += i + "/"
pathEtc = pathWork + "etc"
sys.path.append(pathEtc)

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

if 'ail' in config:
    ail_url = config['ail']['url']
    ail_key = config['ail']['apikey']

if 'redis' in config:
    red = redis.Redis(host=config['redis']['host'], port=config['redis']['port'], charset="utf-8", decode_responses=True)
else:
    red = redis.Redis(host='localhost', port=6379, charset="utf-8", decode_responses=True)


def jsonCreation(all_domains, domainMatching, variationMatching, certificat):
    json_output = dict()
    json_output["certificat"] = certificat
    json_output["domains"] = all_domains
    json_output["domain_matching"] = domainMatching
    json_output["variation_matching"] = variationMatching

    with open(os.path.join(pathOutput, domainMatching), "w") as write_file:
        json.dumps(json_output, write_file)


def get_ct():
    sub = red.pubsub()    
    sub.subscribe('ct-certs', ignore_subscribe_messages=False) 

    for m in sub.listen():
        if type(m['data']) is not int:
            cert_der = base64.b64decode(m['data'].rstrip())

            x509 = X509.load_cert_string(cert_der, X509.FORMAT_DER)
            try:
                subject = x509.get_subject().as_text()
                subject = subject.replace("CN=", "")
            except:
                subject = ""
                pass

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

                for dm in domainList:
                    if len(domain.split(".")) >= len(dm.split(".")):

                        reduceDm = domain.split(".")
                        while len(reduceDm) > len(dm.split(".")):
                            reduceDm = reduceDm[1:]

                        reduceDm[-1] = reduceDm[-1].rstrip("\n")

                        if reduceDm == dm.split("."):
                            print("\n!!! FIND A DOMAIN !!!")
                            d = domain.rstrip('\n')
                            print(f"{d} matching with {dm}")
                            jsonCreation(all_domains, domain, dm, m['data'].rstrip())
        



# If domain begin with * or www
def deleteHead(domain):
    if domain.split(".")[0] == "*" or domain.split(".")[0] == "www":
        locDomain = ""
        for element in domain.split(".")[1:]:
            locDomain += element + "."

        locDomain = locDomain[:-1].rstrip("\n")

        return locDomain
    return domain



if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("-fd", "--filedomain", help="File containing domain name. A text file is required.")
    parser.add_argument("-dn", "--domainName", nargs="+", help="list of domain name")

    parser.add_argument("-o", "--output", help="path to ouput location, default: ../output")

    args = parser.parse_args()

    domainList = list()

    pathOutput = args.output
    if not pathOutput:
        if not os.path.isdir(pathWork + "output"):
            os.mkdir(pathWork + "output")

    if args.filedomain:
        if args.filedomain.split(".")[-1] != "txt":
            print("[-] File need to be text")
            exit(-1)

        with open(args.filedomain, "r") as read_file:
            for lines in read_file.readlines():
                domainList.append(lines.rstrip("\n"))
    elif args.domainName:
        domainList = args.domainName
    else:
        print("[-] No domain name given")
        exit(-1)


    """with open("./ct_domain.txt", "r") as read_file:
        for domain in read_file.readlines():
            domain = deleteHead(domain)

            for dm in domainList:
                if len(domain.split(".")) >= len(dm.split(".")):

                    reduceDm = domain.split(".")
                    while len(reduceDm) > len(dm.split(".")):
                        reduceDm = reduceDm[1:]

                    reduceDm[-1] = reduceDm[-1].rstrip("\n")

                    if reduceDm == dm.split("."):
                        print("\n!!! FIND A DOMAIN !!!")
                        d = domain.rstrip('\n')
                        print(f"{d} matching with {dm}")"""

    while True:
        get_ct()
