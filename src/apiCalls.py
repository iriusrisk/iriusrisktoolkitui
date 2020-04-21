import requests
import json
from lxml import etree
from requests_toolbelt import MultipartEncoder


def postProduct(urlServer, product, apiToken, file):
    urlServer=parseUrl(urlServer)
    url = urlServer+"/api/v1/products/upload"
    f = open(file, 'rb')
    payload = {        
        'ref' : product,
        'name' : product,
        'type' : 'STANDARD',
        'fileName': ('filename', f, 'application/xml')
    }
    m = MultipartEncoder(payload)
    

    headers = {
        'api-token': apiToken,
        'Content-Type': m.content_type
    }

    response = requests.post(url, data=m, headers=headers)
    f.close()
    return response

def getProduct(urlServer, product, apiToken):
    urlServer=parseUrl(urlServer)
    url = urlServer+"/api/v1/products/"+product
    payload = {
        "Content-Disposition" : "forma-data",
        
    }
    headers = {
        'Content-Type': "multipart/form-data",
        'api-token': apiToken,
        'accept' : 'application/json'
        }

    response = requests.request("GET", url, data=payload, headers=headers)
    
    return response

def removeProduct(urlServer, product, apiToken):
    urlServer=parseUrl(urlServer)
    url = urlServer+"/api/v1/products/"+product
    payload = {
        "Content-Disposition" : "forma-data",
        
    }
    headers = {
        'Content-Type': "multipart/form-data",
        'api-token': apiToken,
        'accept' : 'application/xml'
        }

    response = requests.request("DELETE", url, data=payload, headers=headers)

    return response


def runRulesByProduct(urlServer, product, apiToken):
    urlServer=parseUrl(urlServer)
    url = urlServer+"/api/v1/rules/product/"+product
    payload = {
        "Content-Disposition" : "forma-data",
        "jsonData": {
            "deleteCountermeasures": False
        }   
    }
    headers = {
        'Content-Type': "multipart/form-data",
        'api-token': apiToken,
        'accept' : 'application/xml'
        }

    response = requests.request("PUT", url, data=payload, headers=headers)

    return response

def postLibrary(urlServer, lib, apiToken, file):
    urlServer=parseUrl(urlServer)
    url = urlServer+"/api/v1/products/upload"

    payload = {        
        'ref' : lib,
        'name' : lib,
        'type' : 'LIBRARY',
        'fileName': ('filename', open(file, 'rb'), 'application/xml')
    }
    m = MultipartEncoder(payload)
    

    headers = {
        'api-token': apiToken,
        'Content-Type': m.content_type
    }

    response = requests.post(url, data=m, headers=headers)
    return response

def getLibrary(urlServer, lib, apiToken):
    urlServer=parseUrl(urlServer)
    url = urlServer+"/api/v1/libraries/"+lib
    payload = {
        "Content-Disposition" : "forma-data",
        
    }
    headers = {
        'Content-Type': "multipart/form-data",
        'api-token': apiToken,
        'accept' : 'application/xml'
            }

    response = requests.request("GET", url, data=payload, headers=headers)
    
    return response

def removeLibrary(urlServer, lib, apiToken):
    urlServer=parseUrl(urlServer)
    url = urlServer+"/api/v1/libraries/"+lib
    payload = {
        "Content-Disposition" : "forma-data",
        
    }
    headers = {
        'Content-Type': "multipart/form-data",
        'api-token': apiToken,
        'accept' : 'application/xml'
        }

    

    return requests.request("DELETE", url, data=payload, headers=headers)


def parseUrl(url):
    if (url.find("https://")==-1 and url.find("http://")==-1):
          url="https://"+url
    return url



