# AIL - feeder from certificate transparency 
This AIL feeder is a generic software to extract informations from certificate transparency 



For the generation of domain name variations: [ail-typo-squatting](https://github.com/ail-project/ail-typo-squatting)



# Requirements

- [redis](https://github.com/redis/redis-py)
- [cerstream](https://github.com/CaliDog/certstream-python)
- [dnspython](https://github.com/rthalley/dnspython)
- [ail-typo-squatting](https://github.com/ail-project/ail-typo-squatting)



# How to run

The program need to run two script to be functional, `bin/ct.py` and `bin/feeder_ct.py`. 

The first one will publish ct informations on a redis db and the other one will subscribe to the channel and use any entry to compare with a list of variations of domain name. Redis pub/sub is used here. 

If a variation match with an entry from redis db, then the variation is send to AIL to crawl the website.

# Usage

~~~~shell
dacru@dacru:~/git/ail-feeder-ct/bin$ python3 feeder_ct.py --help  

usage: feeder_ct.py [-h] [-dn DOMAINNAME [DOMAINNAME ...]] [-fdn FILEDOMAINNAME] [-ats] [-ms] [-o OUTPUT] [-v]

optional arguments:
  -h, --help            show this help message and exit
  -dn DOMAINNAME [DOMAINNAME ...], --domainName DOMAINNAME [DOMAINNAME ...]
                        list of domain name
  -fdn FILEDOMAINNAME, --filedomainName FILEDOMAINNAME
                        file containing list of domain name
  -ats, --ail_typo_squatting
                        Generate Variations for list pass in entry
  -ms, --matching_string
                        Match domain name if variations are in the domain name in any position
  -o OUTPUT, --output OUTPUT
                        path to ouput location, default: ../output
  -v                    verbose, more display
~~~~



# Example of use

Need to pass a text file, where each line is a variation of the original domain name. Variations can be generate at this repository: [ail-typo-squatting](https://github.com/ail-project/ail-typo-squatting)

~~~~shell
dacru@dacru:~/git/ail-feeder-ct/bin$ python3 feeder_ct.py -fd circl.lu.txt
~~~~



It's possible to generate variations directly in the program

~~~~shell
dacru@dacru:~/git/ail-feeder-ct/bin$ python3 feeder_ct.py -dn circl.lu -ats
~~~~



It's possible to search variations in domain name instead of searching only if it's equal

~~~~
dacru@dacru:~/git/ail-feeder-ct/bin$ python3 feeder_ct.py -dn circl.lu -ats -ms
~~~~



# JSON output format

the name of the JSON file will be the domains matching the variation.

if the dns resolving give no result, then the key "dns_resolve" will not be present in the JSON file.

~~~~json
{
	"certificat": "", 
    "domains": [], 
    "domain_matching": "", 
    "variation_matching": "", 
    "dns_resolve": {"A": [], "MX": [], "TXT": [], ...}
}
~~~~



# List of Resource Record use

```
NONE
A
NS
MD
MF
CNAME
SOA
MB
MG
MR
NULL
WKS
PTR
HINFO
MINFO
MX
TXT
RP
AFSDB
X25
ISDN
RT
NSAP
NSAP_PTR
SIG
KEY
PX
GPOS
AAAA
LOC
NXT
SRV
NAPTR
KX
CERT
A6
DNAME
OPT
APL
DS
SSHFP
IPSECKEY
RRSIG
NSEC
DNSKEY
DHCID
NSEC3
NSEC3PARAM
TLSA
HIP
CDS
CDNSKEY
CSYNC
SPF
UNSPEC
EUI48
EUI64
TKEY
TSIG
IXFR
AXFR
MAILB
MAILA
ANY
URI
CAA
TA
DLV
```
