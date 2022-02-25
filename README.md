# AIL - feeder from certificate transparency 
This AIL feeder is a generic software to extract informations from certificate transparency 



For the generation of domain name variations: [ail-typo-squatting](https://github.com/ail-project/ail-typo-squatting)



# Requirements

- [redis](https://github.com/redis/redis-py)
- [cerstream](https://github.com/CaliDog/certstream-python)



# How to run

The program need to run two script to be functional, `bin/ct.py` and `bin/feeder_ct.py`. 

The first one will publish ct informations on a redis db and the other one will subscribe to the channel and use any entry to compare with a list of variations of domain name. Redis pub/sub is used here. 

If a variation match with an entry from redis db, then the variation is send to AIL to crawl the website.

# Usage

~~~~shell
dacru@dacru:~/git/ail-feeder-ct/bin$ python3 feeder_ct.py --help  
usage: feeder_ct.py [-h] -fd FILEDOMAIN

optional arguments:
  -h, --help            show this help message and exit
  -fd FILEDOMAIN, --filedomain FILEDOMAIN
                        File containing domain name. A text file is required.
~~~~



# Example of use

Need to pass a text file, where each line is a variation of the original domain name. Variations can be generate at this repository: [ail-typo-squatting](https://github.com/ail-project/ail-typo-squatting)

~~~~shell
dacru@dacru:~/git/ail-feeder-ct/bin$ python3 feeder_ct.py -fd circl.lu.txt
~~~~

