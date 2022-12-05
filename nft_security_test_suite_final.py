# author name: Ankit Kalra
# last updated: 12-04-2022
# cybersecurity practicum project source code
# this source code is personal academic work

# launch message
print("tool initialized OK")

# load modules
import json
import requests
from web3 import Web3
from time import sleep
import os
import validators
import base64

# document API keys here --- these are unique to the author's account hence these are not to be shared externally 
# *** Secret *** My infura API key goes here
My_Infura_API_Key = ""
# *** Secret *** My EtherScan APIToken goes here
My_EtherScan_API_Key = ""
# *** Secret *** X_RapidAPI_Key goes here
X_RapidAPI_Key = ""

# set some sleep time to honor API rate limits. This can be shortened to (1) or even (0) with a better API pricing plan that allows higher rate limits
nap_time = 5

# ST1 function (Is the creator account verified)
def creator_verified_ST1(token_address, token_ID):
    
    print("running security test ST1: is the creator account verified...")
    rapidAPI_opensea_tokenURL = 'https://opensea-data-query.p.rapidapi.com/api/v1/asset/' + token_address + '/' + token_ID

    headers = {
        "X-RapidAPI-Key": X_RapidAPI_Key,
        "X-RapidAPI-Host": "opensea-data-query.p.rapidapi.com"
    }

    response = requests.request("GET", rapidAPI_opensea_tokenURL, headers=headers)
    creator_config = json.loads(response.text)['creator']['config']
    
    return creator_config

# ST2 function (Is the artwork collection verified)
def collection_verified_ST2(token_address, token_ID):
    
    print("running security test ST2: is the artwork collection verified...")

    # use OpenSea API: https://api.opensea.io/api/v1/asset/{asset_contract_address}/{token_id}/
    rapidAPI_opensea_tokenURL = 'https://opensea-data-query.p.rapidapi.com/api/v1/asset/' + token_address + '/' + token_ID

    headers = {
        "X-RapidAPI-Key": X_RapidAPI_Key,
        "X-RapidAPI-Host": "opensea-data-query.p.rapidapi.com"
    }

    response = requests.request("GET", rapidAPI_opensea_tokenURL, headers=headers)
    collection_slug = json.loads(response.text)['collection']['slug']

    # use OpenSea API: https://api.opensea.io/api/v1/collection/{collection_slug}
    rapidAPI_opensea_tokenURL = 'https://opensea-data-query.p.rapidapi.com/api/v1/collection/' + collection_slug
    response = requests.request("GET", rapidAPI_opensea_tokenURL, headers=headers)
    safelist_request_status = json.loads(response.text)['collection']['safelist_request_status']
    
    return safelist_request_status

# ST3 function (Is the NFT metadata hosted in a centralized database (public or private) OR decentralized (IPFS or Arweave or Filecoin))
def nft_metadata_hosting_ST3(token_address, token_ID):

    print("running security test ST3: is the NFT metadata hosted in a centralized database (public or private) OR decentralized (IPFS or Arweave or Filecoin)...")

    return_response = ""

    decentraldb_word1 = 'ipfs'
    decentraldb_word2 = 'arweave'
    decentraldb_word3 = 'filecoin'

    # define web3 node
    infura_url = f"https://mainnet.infura.io/v3/" + My_Infura_API_Key

    # check if this connection works
    w3 = Web3(Web3.HTTPProvider(infura_url))
    res = w3.isConnected()
    if res != True:
        print("failed to connect to the web3 client. Cannot run security test ST3")
    
    # let's now try to interact with Smart Contract Functions

    # First let's initialize a contract instance using the ABI and the address
    
    # Ethereum uses checksum addresses to minimize the risk of user error in entering the address. The error in web3.py means you entered a non checksum address (all lower case).
    address = Web3.toChecksumAddress(token_address)

    # fetch the ABI of the Smart Contract from Etherscan API
    # OR manually get this from: https://api.etherscan.io/api?module=contract&action=getabi&address=<>&apikey=<>}
    
    ABI_ENDPOINT = 'https://api.etherscan.io/api?module=contract&action=getabi&address='
    sleep(nap_time)
    response = requests.get('%s%s'%(ABI_ENDPOINT, address))
    response_json = response.json()
    abi_status = json.loads(response_json['status'])
    
    if abi_status == 0:
        print("Error retrieving contract ABI or Contract is not verified!")
    
        # use OpenSea API: https://api.opensea.io/api/v1/asset/{asset_contract_address}/{token_id}/
        rapidAPI_opensea_tokenURL = 'https://opensea-data-query.p.rapidapi.com/api/v1/asset/' + token_address + '/' + token_ID

        headers = {
            "X-RapidAPI-Key": X_RapidAPI_Key,
            "X-RapidAPI-Host": "opensea-data-query.p.rapidapi.com"
        }

        response = requests.request("GET", rapidAPI_opensea_tokenURL, headers=headers)
        token_metadata = json.loads(response.text)['token_metadata']
        if token_metadata != None:
            if token_metadata.find(decentraldb_word1) != -1 or token_metadata.find(decentraldb_word2) != -1 or token_metadata.find(decentraldb_word3) != -1:
                return_response = 'decentral'


    else:
        abi_json = json.loads(response_json['result'])
        result = json.dumps(abi_json)

        contract = w3.eth.contract(address=address, abi=result)

        # let's use different public functions of smart contracts to query the blockchain

        try:
            function_metadataURI_response = contract.functions.metadataURI().call()
            if function_metadataURI_response.find(decentraldb_word1) != -1 or function_metadataURI_response.find(decentraldb_word2) != -1 or function_metadataURI_response.find(decentraldb_word3) != -1:
                return_response = 'decentral'

            valid = validators.url(function_metadataURI_response)
            if valid!=True:
                if function_metadataURI_response.find('data:application/json;base64') != -1:
                    return_response = 'onchain'
        except:
            print ("Error found when executing metadataURI function in the contract!")

            try:
                function_tokenURI_response = contract.functions.tokenURI(tokenID).call()
                if function_tokenURI_response.find(decentraldb_word1) != -1 or function_tokenURI_response.find(decentraldb_word2) != -1 or function_tokenURI_response.find(decentraldb_word3) != -1:
                    return_response = 'decentral'
                
                valid = validators.url(function_tokenURI_response)
                if valid!=True:
                    if function_tokenURI_response.find('data:application/json;base64') != -1:
                        return_response = 'onchain'
                
                        function_tokenURI_response_data = function_tokenURI_response.split("data:application/json;base64,",1)[1]
                                        
                        img_data = "b'" + function_tokenURI_response_data + "'"
                        with open("imageToSave.png", 'wb') as fh:
                            fh.write(base64.b64decode(img_data))

            except:
                print ("Error found when executing tokenURI function in the contract!")

                try:
                    function_baseTokenURI_response = contract.functions.baseTokenURI().call()
                    if function_baseTokenURI_response.find(decentraldb_word1) != -1 or function_baseTokenURI_response.find(decentraldb_word2) != -1 or function_baseTokenURI_response.find(decentraldb_word3) != -1:
                        return_response = 'decentral'
                    
                    valid = validators.url(function_baseTokenURI_response)
                    if valid!=True:
                        if function_baseTokenURI_response.find('data:application/json;base64') != -1:
                            return_response = 'onchain'
                
                except:
                    print ("Error found when executing baseTokenURI function in the contract!")

    return return_response

# ST4 function (Is the NFT metadata URI mutable in the contract)
def nft_metadata_mutable_ST4(token_address, token_ID):
    
    print("running security test ST4: is the NFT metadata URI mutable in the contract...")

    #This security test needs access to the smart contract source code. Define the Etherscan API here to fetch the source code:
    Etherscan_ContractSourceCode_API = 'https://api.etherscan.io/api?module=contract&action=getsourcecode&address=' + token_address + '&apikey=' + My_EtherScan_API_Key
    
    sleep(nap_time)
    response = requests.get(Etherscan_ContractSourceCode_API)
    data = json.loads(response.text)['result'][0]['SourceCode']

    # let's analyze the different public functions of the code to find potential red flags of metadata mutability
    return_response = ''

    data_splits = data.split()
    counter = 0
    func_loc = 0

    for word in data_splits:
        if (word.lower().find('function') != -1):
            func_loc = counter
            
            if (data_splits[func_loc+1].lower().find('base') != -1 or data_splits[func_loc+1].lower().find('set') != -1) \
            and (data_splits[func_loc+1].lower().find('uri') != -1) \
            and (data_splits[func_loc+1].lower().find('string') != -1) \
            and (data_splits[func_loc+3].lower().find('public') != -1 or data_splits[func_loc+4].lower().find('public') != -1 \
            or data_splits[func_loc+5].lower().find('public') != -1 or data_splits[func_loc+3].lower().find('external') != -1 or data_splits[func_loc+4].lower().find('external') != -1 \
            or data_splits[func_loc+5].lower().find('external') != -1) \
            and (data_splits[func_loc+5].lower().find('{') != -1 or data_splits[func_loc+6].lower().find('{') != -1 \
            or data_splits[func_loc+7].lower().find('{') != -1 or data_splits[func_loc+8].lower().find('{') != -1):
                
                func_name = 'function ' + data_splits[func_loc+1]
                
                
                if data.find(func_name) != -1:
                    if data.find('public', data.find(func_name)) != -1:
                        if data.find('public', data.find(func_name)) - data.find(func_name) < 60:
                            
                            #now that we know that the function exists, let's find out who can call it:
                            #reference: https://docs.openzeppelin.com/contracts/4.x/access-control
                            #find location of ')'
                            closedbr_loc = data.find(')', data.find(func_name), data.find('public', data.find(func_name)))
                            opencurl_loc = data.find('{', data.find('public', data.find(func_name)))
                            whocancallfn = data[closedbr_loc+1:opencurl_loc]
                            whocancallfn = whocancallfn.replace("public", "")
                            if whocancallfn.strip() == '':
                                return_response = 'mutable by: anyone'
                            else:
                                if whocancallfn.find('override') != -1:
                                    whocancallfn = whocancallfn.replace("override", "") 
                                return_response = 'mutable by: ' + whocancallfn.strip()
                
                if data.find(func_name) != -1:
                    if data.find('external', data.find(func_name)) != -1:
                        if data.find('external', data.find(func_name)) - data.find(func_name) < 60:
                            
                            #now that we know that the function exists, let's find out who can call it:
                            #reference: https://docs.openzeppelin.com/contracts/4.x/access-control
                            #find location of ')'
                            closedbr_loc = data.find(')', data.find(func_name), data.find('external', data.find(func_name)))
                            opencurl_loc = data.find('{', data.find('external', data.find(func_name)))
                            whocancallfn = data[closedbr_loc+1:opencurl_loc]
                            whocancallfn = whocancallfn.replace("external", "")
                            if whocancallfn.strip() == '':
                                return_response = 'mutable by: anyone'
                            else:
                                if whocancallfn.find('override') != -1:
                                    whocancallfn = whocancallfn.replace("override", "") 
                                return_response = 'mutable by: ' + whocancallfn.strip()
        
        counter = counter + 1

    return return_response

# ST5 function (Is the digital asset (NFT) hosted in a centralized database (public or private) OR decentralized (IPFS or Arweave or Filecoin) OR on chain)
def nft_hosting_ST5(token_address, token_ID):
    
    print("running security test ST5: is the digital asset (NFT) hosted in a centralized database (public or private) OR decentralized (IPFS or Arweave or Filecoin) OR on chain...")

    function_tokenURI_ext = 0
    return_response = ""

    decentraldb_word1 = 'ipfs'
    decentraldb_word2 = 'arweave'
    decentraldb_word3 = 'filecoin'

    # Define the OpenSea API
    rapidAPI_opensea_tokenURL = 'https://opensea-data-query.p.rapidapi.com/api/v1/asset/' + token_address + '/' + token_ID

    headers = {
        "X-RapidAPI-Key": X_RapidAPI_Key,
        "X-RapidAPI-Host": "opensea-data-query.p.rapidapi.com"
    }

    # define web3 node
    infura_url = f"https://mainnet.infura.io/v3/" + My_Infura_API_Key

    # check if this connection works
    w3 = Web3(Web3.HTTPProvider(infura_url))
    res = w3.isConnected()
    if res != True:
        print("failed to connect to the web3 client (Infura). This means we cannot fully run security test ST5")
    
    # let's now try to interact with Smart Contract Functions

    # First let's initialize a contract instance using the ABI and the address
    
    # Ethereum uses checksum addresses to minimize the risk of user error in entering the address. The error in web3.py means you entered a non checksum address (all lower case).
    address = Web3.toChecksumAddress(token_address)

    # fetch the ABI of the Smart Contract from Etherscan API
    # OR manually get this from: https://api.etherscan.io/api?module=contract&action=getabi&address=<>&apikey=<>
    
    ABI_ENDPOINT = 'https://api.etherscan.io/api?module=contract&action=getabi&address='
    sleep(nap_time)
    response = requests.get('%s%s'%(ABI_ENDPOINT, address))
    response_json = response.json()
    abi_status = json.loads(response_json['status'])
    
    # Let's first try the opensea API approach
    OpenSea_API_respose = requests.request("GET", rapidAPI_opensea_tokenURL, headers=headers)
    
    image_original_url = json.loads(OpenSea_API_respose.text)['image_original_url']
    
    if image_original_url != None:
        if image_original_url.find(decentraldb_word1) != -1 or image_original_url.find(decentraldb_word2) != -1 or image_original_url.find(decentraldb_word3) != -1:
                return_response = 'decentral'
        else:
            if image_original_url.find('googleapi') != -1 or image_original_url.find('s3') != -1:
                return_response = 'central'
    
    else:
        if abi_status == 0:
            print("Error retrieving contract ABI or Contract is not verified!")
        
            # use OpenSea API: https://api.opensea.io/api/v1/asset/{asset_contract_address}/{token_id}/
            rapidAPI_opensea_tokenURL = 'https://opensea-data-query.p.rapidapi.com/api/v1/asset/' + token_address + '/' + token_ID

            headers = {
                "X-RapidAPI-Key": X_RapidAPI_Key,
                "X-RapidAPI-Host": "opensea-data-query.p.rapidapi.com"
            }

            response = requests.request("GET", rapidAPI_opensea_tokenURL, headers=headers)
            token_metadata = json.loads(response.text)['token_metadata']
            if token_metadata != None:
                if token_metadata.find(decentraldb_word1) != -1 or token_metadata.find(decentraldb_word2) != -1 or token_metadata.find(decentraldb_word3) != -1:
                    return_response = 'decentral'

        else:
             
            abi_json = json.loads(response_json['result'])
            result = json.dumps(abi_json)

            contract = w3.eth.contract(address=address, abi=result)

            # let's use different public functions of smart contracts to query the blockchain

            function_tokenURI_response = contract.functions.tokenURI(tokenID).call()
            
            #if metadata is hosted on the blockchain
            valid = validators.url(function_tokenURI_response)
            if valid!=True:
                if function_tokenURI_response.find('data:application/json;base64') != -1:
                    return_response = 'onchain'

            #if metadata is hosted hosted on ipfs
            elif function_tokenURI_response.find(decentraldb_word1) != -1:
                function_tokenURI_response_ipfs = function_tokenURI_response.split("//",1)[1]
                function_tokenURI_response_ipfs_data = requests.get('https://ipfs.io/ipfs/' + function_tokenURI_response_ipfs)
                function_tokenURI_response_ipfs_data_json = function_tokenURI_response_ipfs_data.json()
                image_url = function_tokenURI_response_ipfs_data_json['image']
                
                if image_url.find(decentraldb_word1) != -1 or image_url.find(decentraldb_word2) != -1 or image_url.find(decentraldb_word3) != -1:
                    return_response = 'decentral'
                else:
                    if image_url.find('googleapi') != -1 or image_url.find('s3') != -1:
                        return_response = 'central'
            
            #if metadata is hosted hosted on opensea
            elif function_tokenURI_response.find('opensea') != -1:
                function_tokenURI_response_opensea_data = requests.get(function_tokenURI_response)
                function_tokenURI_response_opensea_data_json = function_tokenURI_response_opensea_data.json()
                image_url = function_tokenURI_response_opensea_data_json['image']
                
                if image_url.find(decentraldb_word1) != -1 or image_url.find(decentraldb_word2) != -1 or image_url.find(decentraldb_word3) != -1:
                    return_response = 'decentral'
                else:
                    if image_url.find('googleapi') != -1 or image_url.find('s3') != -1:
                        return_response = 'central'
            
            #if metadata is hosted hosted on arweave
            elif function_tokenURI_response.find(decentraldb_word2) != -1:
                function_tokenURI_response_opensea_data = requests.get(function_tokenURI_response)
                function_tokenURI_response_opensea_data_json = function_tokenURI_response_opensea_data.json()
                image_url = function_tokenURI_response_opensea_data_json['image']
                
                if image_url.find(decentraldb_word1) != -1 or image_url.find(decentraldb_word2) != -1 or image_url.find(decentraldb_word3) != -1:
                    return_response = 'decentral'
                else:
                    if image_url.find('googleapi') != -1 or image_url.find('s3') != -1:
                        return_response = 'central'
            
            #if metadata is hosted hosted on filecoin
            elif function_tokenURI_response.find(decentraldb_word3) != -1:
                function_tokenURI_response_opensea_data = requests.get(function_tokenURI_response)
                function_tokenURI_response_opensea_data_json = function_tokenURI_response_opensea_data.json()
                image_url = function_tokenURI_response_opensea_data_json['image']
                
                if image_url.find(decentraldb_word1) != -1 or image_url.find(decentraldb_word2) != -1 or image_url.find(decentraldb_word3) != -1:
                    return_response = 'decentral'
                else:
                    if image_url.find('googleapi') != -1 or image_url.find('s3') != -1:
                        return_response = 'central'


    return return_response

# ST6 function (Is the smart contract verified)
def contract_verify_ST6(token_address, token_ID):
    
    print("running security test ST6: is the smart contract verified...")

    return_response = ""

    # define web3 node
    infura_url = f"https://mainnet.infura.io/v3/" + My_Infura_API_Key

    # check if this connection works
    w3 = Web3(Web3.HTTPProvider(infura_url))
    res = w3.isConnected()
    if res != True:
        print("failed to connect to the web3 client. Cannot run security test ST3")
    
    # Now try to interact with Smart Contract Functions

    # Initialize a contract instance using the ABI and the address
    
    # Ethereum uses checksum addresses to minimize the risk of user error in entering the address. The error in web3.py means you entered a non checksum address (all lower case).
    address = Web3.toChecksumAddress(token_address)

    # fetch the ABI of the Smart Contract from Etherscan API
    # OR manually get this from: https://api.etherscan.io/api?module=contract&action=getabi&address=<>&apikey=<>
    
    ABI_ENDPOINT = 'https://api.etherscan.io/api?module=contract&action=getabi&address='
    try_count = 0
    while try_count < 3:
        try_count = try_count + 1
        try:
            sleep(nap_time)
            response = requests.get('%s%s'%(ABI_ENDPOINT, address))
            response_json = response.json()
            abi_status = json.loads(response_json['status'])
            
            if abi_status == 0:
                return_response = 'not verified'
            elif abi_status == 1:
                return_response = 'verified'
                try_count = 3
        except:
            print("Connection refused by the server..")
            print("Trying again in 5 seconds")
            sleep(nap_time)

    return return_response

# ST7 function (Is the locally cached artwork different than the original asset)
def image_caching_validation_ST7(token_address, token_ID):

    print("running security test ST7: is the locally cached artwork different than the original asset...")

    return_response = ""

    decentraldb_word1 = 'ipfs'
    decentraldb_word2 = 'arweave'
    decentraldb_word3 = 'filecoin'

    tokenID = int(token_ID)

    # Define the OpenSea API
    rapidAPI_opensea_tokenURL = 'https://opensea-data-query.p.rapidapi.com/api/v1/asset/' + token_address + '/' + token_ID

    headers = {
        "X-RapidAPI-Key": X_RapidAPI_Key,
        "X-RapidAPI-Host": "opensea-data-query.p.rapidapi.com"
    }

    # define web3 node
    infura_url = f"https://mainnet.infura.io/v3/" + My_Infura_API_Key

    # check if this connection works
    w3 = Web3(Web3.HTTPProvider(infura_url))
    res = w3.isConnected()
    if res != True:
        print("failed to connect to the web3 client (Infura). This means we cannot fully run security test ST7")
    
    # let's now try to interact with Smart Contract Functions

    # First let's initialize a contract instance using the ABI and the address
    
    # Ethereum uses checksum addresses to minimize the risk of user error in entering the address. The error in web3.py means you entered a non checksum address (all lower case).
    address = Web3.toChecksumAddress(token_address)

    # fetch the ABI of the Smart Contract from Etherscan API
    # OR manually get this from: https://api.etherscan.io/api?module=contract&action=getabi&address=<>&apikey=<>
    
    ABI_ENDPOINT = 'https://api.etherscan.io/api?module=contract&action=getabi&address='
    sleep(nap_time)
    response = requests.get('%s%s'%(ABI_ENDPOINT, address))
    response_json = response.json()
    abi_status = json.loads(response_json['status'])
    # Let's first try the opensea API approach
    OpenSea_API_respose = requests.request("GET", rapidAPI_opensea_tokenURL, headers=headers)
    
    image_original_url = json.loads(OpenSea_API_respose.text)['image_original_url']
    image_original_url_saved = 0

    # get file extension from the url
    if image_original_url != None:
        filename, file_extension = os.path.splitext(image_original_url)
        if file_extension == "":
            file_extension = '.png'
    
        #if image_original_url is hosted hosted on ipfs
        if image_original_url.find(decentraldb_word1) != -1:
            if image_original_url.find('pinata.cloud') != -1:
                image_original_url = image_original_url
            else:
                image_original_url = 'https://ipfs.io/ipfs/' + image_original_url.split("//",1)[1]

        #check http response code
        r = ''
        try_count = 0
        while try_count < 3:
            try_count = try_count + 1
            try:
                r = requests.head(image_original_url)

                if r.status_code == 200:
                    r = requests.get(image_original_url)
                    return_response = ""
                    with open(token_ID + "image_original" + file_extension, 'wb') as f:
                        f.write(r.content)
                    image_original_url_saved = 1
                    return_response = "Original image saved for user review as " + token_ID + "image_original" + file_extension
                elif r.status_code == 401:
                    return_response = "Original image is not accessible"
                    image_original_url_saved = 0
                break
            except:
                print("Connection refused by the server..")
                print("Trying again in 5 seconds")
                sleep(nap_time)
                return_response = "Original image is not accessible"
                continue
    
    if abi_status == 0:
        print("Error retrieving contract ABI or Contract is not verified. This means we may not be able to fully run tests ST7.")
        if image_original_url_saved == 0:
            return_response = "Original image is not accessible"

    elif abi_status != 0 and image_original_url_saved == 0:
        abi_json = json.loads(response_json['result'])
        result = json.dumps(abi_json)

        contract = w3.eth.contract(address=address, abi=result)

        try:
            # let's use different public functions of smart contracts to query the blockchain
            function_tokenURI_response = contract.functions.tokenURI(tokenID).call()
            
            #if the asset on the blockchain
            valid = validators.url(function_tokenURI_response)
            if valid!=True:
                if function_tokenURI_response.find('data:application/json;base64') != -1:
                    return_response = 'onchain'

                    function_tokenURI_response_data = function_tokenURI_response.split("data:application/json;base64,",1)[1]
                                        
                    img_data = "b'" + function_tokenURI_response_data + "'"
                    with open(token_ID + ".png", 'wb') as fh:
                        fh.write(base64.b64decode(img_data))
                        return_response = "Original image saved for user review as " + token_ID + ".png"

            #if metadata is hosted hosted on ipfs
            elif function_tokenURI_response.find(decentraldb_word1) != -1:
                if function_tokenURI_response.find('pinata.cloud') != -1:
                    function_tokenURI_response_ipfs = function_tokenURI_response
                else:
                    function_tokenURI_response_ipfs = function_tokenURI_response.split("//",1)[1]
                
                r = ''
                try_count = 0
                while try_count < 3:
                    try_count = try_count + 1
                    try:
                        if function_tokenURI_response_ipfs.find('pinata.cloud') != -1:
                            function_tokenURI_response_ipfs_data = requests.get(function_tokenURI_response_ipfs)
                        else:
                            function_tokenURI_response_ipfs_data = requests.get('https://ipfs.io/ipfs/' + function_tokenURI_response_ipfs)
                        
                        function_tokenURI_response_ipfs_data_json = function_tokenURI_response_ipfs_data.json()
                        image_url = function_tokenURI_response_ipfs_data_json['image']
                        
                        if image_url.find('pinata.cloud') != -1:
                            image_url_ipfs_gateway = image_url
                        else:
                            image_url_ipfs_gateway = 'https://ipfs.io/ipfs/' + image_url.split("//",1)[1]
                        
                        if image_original_url_saved == 0 and image_original_url != image_url_ipfs_gateway:
                            r = requests.head(image_url_ipfs_gateway)
                                                
                            # get file extension from the url
                            filename, file_extension = os.path.splitext(image_url_ipfs_gateway)
                            if file_extension == "":
                                file_extension = '.png'
                            
                            if r.status_code == 200:
                                r = requests.get(image_url_ipfs_gateway)
                                return_response = ""
                                with open(token_ID + "image_original" + file_extension, 'wb') as f:
                                    f.write(r.content)
                                    return_response = "Original image saved for user review as " + token_ID + "image_original" + file_extension
                            elif r.status_code == 401:
                                return_response = "Original image is not accessible"
                        
                        break
                    except:
                        print("Connection refused by the server..")
                        print("Trying again in 5 seconds")
                        sleep(nap_time)
                        return_response = "Original image is not accessible"
                        continue
            
            #if metadata is hosted hosted on opensea
            elif function_tokenURI_response.find('opensea') != -1:
                print(function_tokenURI_response)
                function_tokenURI_response_opensea_data = requests.get(function_tokenURI_response)
                print (function_tokenURI_response_opensea_data.text)
                function_tokenURI_response_opensea_data_json = function_tokenURI_response_opensea_data.json()
                image_url = function_tokenURI_response_opensea_data_json['image']
                
                r = ''
                try_count = 0
                while try_count < 3:
                    try_count = try_count + 1
                    try:
                        if image_original_url_saved == 0 and image_original_url != image_url:
                            r = requests.head(image_url)

                            # get file extension from the url
                            filename, file_extension = os.path.splitext(image_url)
                            if file_extension == "":
                                file_extension = '.png'

                            if r.status_code == 200:
                                r = requests.get(image_url)
                                return_response = ""
                                with open(token_ID + "image_original" + file_extension, 'wb') as f:
                                    f.write(r.content)
                                    return_response = "Original image saved for user review as " + token_ID + "image_original" + file_extension
                            elif r.status_code == 401:
                                return_response = "Original image is not accessible"
                        
                        break
                    except:
                        print("Connection refused by the server..")
                        print("Trying again in 5 seconds")
                        sleep(nap_time)
                        return_response = "Original image is not accessible"
                        continue
            
            #if metadata is hosted hosted on arweave
            elif function_tokenURI_response.find(decentraldb_word2) != -1:
                print(function_tokenURI_response)
                function_tokenURI_response_opensea_data = requests.get(function_tokenURI_response)
                print (function_tokenURI_response_opensea_data.text)
                function_tokenURI_response_opensea_data_json = function_tokenURI_response_opensea_data.json()
                image_url = function_tokenURI_response_opensea_data_json['image']
                
                r = ''
                try_count = 0
                while try_count < 3:
                    try_count = try_count + 1
                    try:
                        if image_original_url_saved == 0 and image_original_url != image_url:
                            r = requests.head(image_url)

                            # get file extension from the url
                            filename, file_extension = os.path.splitext(image_url)
                            if file_extension == "":
                                file_extension = '.png'

                            if r.status_code == 200:
                                r = requests.get(image_url)
                                return_response = ""
                                with open(token_ID + "image_original" + file_extension, 'wb') as f:
                                    f.write(r.content)
                                    return_response = "Original image saved for user review as " + token_ID + "image_original" + file_extension
                            elif r.status_code == 401:
                                return_response = "Original image is not accessible"
                        
                        break
                    except:
                        print("Connection refused by the server..")
                        print("Trying again in 5 seconds")
                        sleep(nap_time)
                        return_response = "Original image is not accessible"
                        continue
            
            #if metadata is hosted hosted on filecoin
            if function_tokenURI_response.find(decentraldb_word3) != -1:
                print(function_tokenURI_response)
                function_tokenURI_response_opensea_data = requests.get(function_tokenURI_response)
                print (function_tokenURI_response_opensea_data.text)
                function_tokenURI_response_opensea_data_json = function_tokenURI_response_opensea_data.json()
                image_url = function_tokenURI_response_opensea_data_json['image']
                
                r = ''
                try_count = 0
                while try_count < 3:
                    try_count = try_count + 1
                    try:
                        if image_original_url_saved == 0 and image_original_url != image_url:
                            r = requests.head(image_url)

                            # get file extension from the url
                            filename, file_extension = os.path.splitext(image_url)
                            if file_extension == "":
                                file_extension = '.png'

                            if r.status_code == 200:
                                r = requests.get(image_url)
                                return_response = ""
                                with open(token_ID + "image_original" + file_extension, 'wb') as f:
                                    f.write(r.content)
                                    return_response = "Original image saved for user review as " + token_ID + "image_original" + file_extension
                            elif r.status_code == 401:
                                return_response = "Original image is not accessible"
                        
                        break
                    except:
                        print("Connection refused by the server..")
                        print("Trying again in 5 seconds")
                        sleep(nap_time)
                        return_response = "Original image is not accessible"
                        continue
        except:
            print ("Error found when executing tokenURI function in the contract!")
            return_response = "Error found when executing tokenURI function in the contract!"
    return return_response


#Take user inputs
token_address = input("Enter the token address: ")
token_ID = input("Enter the token ID: ")

tokenID = int(token_ID)

#FIRST check the validity of contract address
rapidAPI_opensea_tokenURL = 'https://opensea-data-query.p.rapidapi.com/api/v1/asset_contract/' + token_address

headers = {
    "X-RapidAPI-Key": X_RapidAPI_Key,
    "X-RapidAPI-Host": "opensea-data-query.p.rapidapi.com"
}

response = requests.request("GET", rapidAPI_opensea_tokenURL, headers=headers)
asset_contract_type = json.loads(response.text)['asset_contract_type']

if asset_contract_type == 'unknown':
    print("invalid or out-of-scope contract address. exiting program!")
    exit()

sleep(nap_time)
# call ST1 functions (Is the creator account verified)
st1_response = creator_verified_ST1(token_address, token_ID)
if st1_response == "verified":
    st1_result = 'pass'
else:
    st1_result = 'fail'

sleep(nap_time)
# call ST2 functions (Is the artwork collection verified)
st2_response = collection_verified_ST2(token_address, token_ID)
if st2_response == "verified":
    st2_result = 'pass'
else:
    st2_result = 'fail'

sleep(nap_time)
# call ST3 functions (Is the NFT metadata hosted in a centralized database (public or private) OR decentralized (IPFS or Arweave or Filecoin))
st3_response = nft_metadata_hosting_ST3(token_address, token_ID)
if st3_response == "decentral":
    st3_result = 'pass'
elif st3_response == "onchain":
    st3_result = 'onchain'
else:
    st3_result = 'fail'

sleep(nap_time)
# call ST4 functions (Is the NFT metadata URI mutable in the contract)
st4_response = nft_metadata_mutable_ST4(token_address, token_ID)
if st4_response.find('mutable by') != -1:
    st4_result = 'fail'
else:
    st4_result = 'pass'

sleep(nap_time)
# call ST5 functions (Is the digital asset (NFT) hosted in a centralized database (public or private) OR decentralized (IPFS or Arweave or Filecoin) OR on chain)
st5_response = nft_hosting_ST5(token_address, token_ID)
if st5_response == "decentral":
    st5_result = 'pass'
elif st5_response == "central" or st5_response == "":
    st5_result = 'fail'
elif st5_response == "onchain":
    st5_result = 'onchain'

sleep(nap_time)
# call ST6 functions (Is the smart contract verified)
st6_response = contract_verify_ST6(token_address, token_ID)
if st6_response == "verified":
    st6_result = 'pass'
elif st6_response == "not verified":
    st6_result = 'fail'

sleep(nap_time)
# call ST7 functions (Is the locally cached artwork different than the original asset)
st7_response = image_caching_validation_ST7(token_address, token_ID)
if st7_response.find('Original image saved for user review') != -1:
    st7_result = 'pass'
elif st7_response == "Original image is not accessible":
    st7_result = 'fail'
elif st7_response == "Error found when executing tokenURI function in the contract!":
    st7_result = st7_response


#publish security test results
print('\n***Tests completed successfully. Results summary***')
print('\nToken contract address: ', token_address)
print('Token ID: ', token_ID)

if st1_result == 'pass':
    print('\nST1: Pass. Creator account is verified on the marketplace')
elif st1_result == 'fail':
    print('\nST1: Fail. Creator account is not verified on the marketplace')

if st2_result == 'pass':
    print('ST2: Pass. Artwork collection is verified on the marketplace')
elif st2_result == 'fail':
    print('ST2: Fail. Artwork collection is not verified on the marketplace')

if st3_result == 'pass':
    print('ST3: Pass. Asset metadata is hosted decentrally')
elif st3_result == 'fail':
    print('ST3: Fail. Asset metadata is hosted centrally in a public or private repository')
elif st3_result == 'onchain':
    print('ST3: Pass. Asset is fully on the blockchain')

if st4_result == 'pass':
    print('ST4: Pass. Asset metadata URI is non-mutable')  
elif st4_result == 'fail':
    print('ST4: Fail. Asset metadata URI is', st4_response)

if st5_result == 'pass':
    print('ST5: Pass. Asset is hosted decentrally')
elif st5_result == 'fail':
    print('ST5: Fail. Asset is hosted centrally in a public or private repository')
elif st5_result == 'onchain':
    print('ST5: Pass. Asset is fully on the blockchain')

if st6_result == 'pass':
    print('ST6: Pass. Asset contract is verified')
elif st6_result == 'fail':
    print('ST6: Fail. Asset contract is not verified')

if st7_result == 'pass':
    print('ST7:', st7_response)
elif st7_result == 'fail':
    print('ST7: Fail. Original image is currently not accessible')
else:
    print('ST7:', st7_result)

#publish overall asset risk rating
risk_rating = 'Low'
if st3_result == 'fail' or st5_result == 'fail' or st6_result == 'fail' or st7_result == 'fail':
    risk_rating = 'High'
elif st4_result == 'fail':
    risk_rating = 'Moderate'
elif st1_result == 'fail' or st2_result == 'fail':
    risk_rating = 'Low'

print ('\nOverall security risk rating for the asset: ', risk_rating)

print('\n***end of results summary***\n')