import idna
import redis
import base64
from M2Crypto import X509

import sys
import signal

red = redis.Redis(host='localhost', port=6379, charset="utf-8", decode_responses=True, db=3)

sub = red.pubsub()    
sub.subscribe('ct-certs', ignore_subscribe_messages=False) 

cp = 0

def signal_handler(sig, frame):
    # print('You pressed Ctrl+C!')
    print()
    sys.exit(0)

def get_ct():
    global sub, red, cp

    signal.signal(signal.SIGINT, signal_handler)

    try:
        m = sub.get_message()
    except:
        red = redis.Redis(host='localhost', port=6379, charset="utf-8", decode_responses=True, db=3)
        sub = red.pubsub()
        sub.subscribe('ct-certs', ignore_subscribe_messages=False)
        m = sub.get_message()

    if m:
        if type(m['data']) is not int:
            cert_der = base64.b64decode(m['data'].rstrip())

            x509 = X509.load_cert_string(cert_der, X509.FORMAT_DER)
            try:
                subject = x509.get_subject().as_text()
                subject = subject.replace("CN=", "")
                # subject contain C, ST, O ...
                subject = subject.split(" ")[-1]
            except:
                subject = ""

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
                try:
                    domain = idna.decode(domain)
                except:
                    break
                for letter in domain:
                    if ord(letter) > 127:
                        # print(f"found one letter: {letter}\n")
                        if red.zscore("letters", letter):
                            red.zincrby("letters", 1, letter)
                        else:
                            red.zadd("letters", {letter: 1})
                            cp += 1
                            print(f"\r[+] Found {cp} differents letters", end="")

    

# If domain begin with *
def deleteHead(domain):
    if domain.split(".")[0] == "*" or domain.split(".")[0] == "www":
        locDomain = ""
        for element in domain.split(".")[1:]:
            locDomain += element + "."

        locDomain = locDomain[:-1].rstrip("\n")

        return locDomain
    return domain



while True:
    get_ct()
