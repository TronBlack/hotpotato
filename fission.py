#!/usr/bin/env python3
# Bounce an asset to an addres you don't own
# Reads addresses from <ip>.addresses.json in the same folder

#If you need pip
#    sudo easy_install pip

#If you need tinydb
#    sudo pip install tinydb

import subprocess
import json
from tinydb import TinyDB, Query
from tinydb.operations import set
import socket
import time
import os
import sys

#Set this to your raven-cli program
cli = "raven-cli"

mode =  "-testnet"
rpc_port = 18766
#mode =  "-regtest"
#rpc_port = 18443

asset="HOTPOTATO*"
extension=".addresses.json"

#Set this information in your raven.conf file (in datadir, not testnet3)
rpc_user = 'rpcuser'
rpc_pass = 'rpcpass555'

if os.name != "nt":
    import fcntl
    import struct

    def get_interface_ip(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s',
                                ifname[:15]))[20:24])

def get_lan_ip():
    ip = socket.gethostbyname(socket.gethostname())
    if ip.startswith("127.") and os.name != "nt":
        interfaces = [
            "eth0",
            "eth1",
            "eth2",
            "wlan0",
            "wlan1",
            "wifi0",
            "ath0",
            "ath1",
            "ppp0",
            ]
        for ifname in interfaces:
            try:
                ip = get_interface_ip(ifname)
                break
            except IOError:
                pass
    return ip


def get_rpc_connection():
    from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
    connection = "http://%s:%s@127.0.0.1:%s"%(rpc_user, rpc_pass, rpc_port)
    #print("Connection: " + connection)
    rpc_conn = AuthServiceProxy(connection)
    return(rpc_conn)
    
rpc_connection = get_rpc_connection()

def listmyassets(filter):
    result = rpc_connection.listmyassets(filter)
    return(result) 

def getaddressesbyaccount(account):
    result = rpc_connection.getaddressesbyaccount(account)
    return(result) 

def rpc_call(params):
    process = subprocess.Popen([cli, mode, params], stdout=subprocess.PIPE)
    out, err = process.communicate()
    return(out)

def generate_blocks(n):
    hashes = rpc_connection.generate(n)
    return(hashes)

def transfer(asset, qty, address):
    result = rpc_connection.transfer(asset, qty, address)
    return(result)

def share_my_addresses(fname):
    db = TinyDB(fname)
    Addresses = Query()
    addresses = getaddressesbyaccount("")
    count = len(addresses)
    print("Adding " + str(count) + " addresses.")
    count = 0
    for address in addresses:
        if count < 10:
            db.upsert({'address': address}, Addresses.address == address)
            count = count + 1

def get_address_files():
    import os
    files = []
    for file in os.listdir("."):
        if file.endswith(extension):
            files.append(file)
    return(files)

def create_master_list_of_addresses():
    Addresses = Query()
    files = get_address_files()
    address_list = []
    fname = get_our_db_file()
    #Loop through all the files and create a master list
    for file in files:
        if file != fname:
            db = TinyDB(file)
            addresses = db.search(Addresses.address != "")
            for address in addresses:
                address_list.append(address['address'])
    #print(result)
    print("Num addresses: " + str(len(address_list)))
    return(address_list)

def get_others_address(master_address_list):
    import random

    if (len(master_address_list) == 0):
        print("You must include address files from other nodes.\nExpected format <ip>"+extension)
        exit(-1)        

    total_addresses = len(master_address_list)
    selected = random.randint(0, total_addresses-1)
    print("Choosing address " + str(selected) + " of " + str(total_addresses) + " is " + master_address_list[selected])
    #Choose an address from the master list
    return(master_address_list[selected])

def transfer_asset(asset, qty, address):
    result = transfer(asset, qty, address)
    return(result[0])

def create_address_file():
    import os
    fname = get_our_db_file()
    if not os.path.isfile(fname):
        print("Filename " + fname + " not found.  Creating...") 
        share_my_addresses(fname)

def get_our_db_file():
    import os.path
    #ip = socket.gethostbyname(socket.gethostname())
    ip = get_lan_ip()
    fname = ip + extension
    return(fname)

def fission(master_address_list, filter):
    transferred = 0
    while (True):
        assets = listmyassets(filter)
        print("Fission asset count: " + str(len(assets)))
        for asset, qty in assets.items():
            if not asset.endswith('!'):  #Only send if not admin token
                if qty > 0:
                    address1 = get_others_address(master_address_list)
                    address2 = get_others_address(master_address_list)
                    if (qty > 1):
                        qty1 = int(qty / 2)
                    else:
                        qty1 = qty

                    qty2 = qty - qty1
                    print("Transfer " + asset + " Qty:" + str(qty1) + " to " + address1)
                    try:
                        txid1 = transfer_asset(asset, qty1, address1)
                        print("TxId 1: " + txid1)
                        transferred=transferred+1
                        print("Asset transfer count: " + str(transferred))
                    except BaseException as err:
                        print("Could not send asset " + asset + ". Possibly already sent, waiting for confirmation.")
                        print(err)
                    
                    print("Transfer " + asset + " Qty:" + str(qty2) + " to " + address2)
                    try:
                        txid2 = transfer_asset(asset, qty2, address2)
                        print("TxId 2: " + txid2)
                        transferred=transferred+1
                        print("Asset transfer count: " + str(transferred))
                    except BaseException as err:
                        print("Could not send asset " + asset + ". Possibly already sent, waiting for confirmation.")
                        print(err)

                    print("")
                else:
                    print("No " + asset + " in wallet.")


        for t in range(0,20):
            sys.stdout.write('.')
            sys.stdout.flush()
            time.sleep(1)
        print("")

def hotpotato(master_address_list, filter):
    transferred = 0
    while (True):
        assets = listmyassets(filter)
        print("Hot Potato asset count: " + str(len(assets)))
        for asset, qty in assets.items():
            if not asset.endswith('!'):  #Only send if not admin token
                address = get_others_address(master_address_list)
                print("Transfer " + asset + " Qty:" + str(qty) + " to " + address)
                try:
                    txid = transfer_asset(asset, qty, address)
                    print("TxId: " + txid)
                    transferred=transferred+1
                    print("Asset transfer count: " + str(transferred))
                except BaseException as err:# JSONRPCException:
                    print("Could not send asset " + asset + ". Possibly already sent, waiting for confirmation.")
                    print(err)
                print("")
        time.sleep(1)



if mode == "-regtest":  #If regtest then mine our own blocks
    import os
    os.system(cli + " " + mode + " generate 400")

create_address_file()
master_list = create_master_list_of_addresses()
fission(master_list, "URANIUM")
#hotpotato(master_list, asset)  #Set to "*" for all.
