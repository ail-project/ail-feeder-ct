import os
import ast
import redis
import pathlib
import argparse
import configparser

pathProg = pathlib.Path(__file__).parent.absolute()

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



def get_ct():    
    sub = red.pubsub()    
    sub.subscribe('ct-certs')    
    for message in sub.listen():
        if message is not None and message.get('data') != 1:    
            domains = ast.literal_eval(message.get('data'))
            for domain in domains:
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

    args = parser.parse_args()

    domainList = list()

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
