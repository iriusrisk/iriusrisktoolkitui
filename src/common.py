import os
home=os.getcwd()
import datetime
from pathlib import Path
import yaml
import requests

def writeConfig(serverUrl, apiToken):
  path=Path.home() / ".iriusrisk.yaml"
  with open(str(path), 'r') as f:
    data = yaml.load(f, Loader=yaml.Loader)
  data['urlServer']=serverUrl
  data['apiToken']=apiToken
  with open(str(path), 'w') as f:
    yaml.dump(data, f, Dumper=yaml.Dumper, default_flow_style=False)


def readConfig():
  apiToken=""
  urlServer=""
  msg=""
  path=Path.home() / ".iriusrisk.yaml"
  # If the file doesn't exist, we shal create the file.
  if not os.path.exists(str(path)):
    with open(str(path), 'w') as f:
      f.write("apiToken: \nurlServer: ")
  with open(str(path), 'r') as f:
    data =yaml.load(f, Loader=yaml.Loader) 
  try:   
    urlServer = data['urlServer']
    apiToken = data['apiToken']
    if urlServer == None:
      urlServer=""
    if apiToken == None:
      apiToken = ""
  except:
    # If the file doesn't contain the necessary parameters
    with open(str(path), 'w') as f:
      f.write("apiToken: \nurlServer: ")
  # If the parameters are empty
  if urlServer == "" or apiToken == "" or urlServer == None or apiToken == None:
    msg="Please fill the fields above."
  else:
    if urlServer[-1] == "/":
      urlServer=urlServer[0:-1]
  return urlServer, apiToken, msg

def testConnection(urlServer, apiToken):
  msg="Testing ..."
  if urlServer[-1] == "/":
    urlServer=urlServer[0:-1]
  # If there is any problem with the url
  try:
    if requests.get(urlServer+"/health").status_code != 200:
      msg="Error connection: wrong URL."
    else:
      # If there is any problem with the api-token
      if requests.get(urlServer+"/api/v1/groups", headers={"api-token":apiToken}).status_code != 200:
        msg="Error connection: wrong api-token." 
      else:
        msg="Connection successfuly!!"
  except:
    msg="Error connection: Server is down."
  
  return msg

def getvalueFromMenu(array, text):
  value=-1
  for i in array:
    text+="%i - %s.\n"%(array.index(i), i)
  
  
  try:
    value=int(input(text))
    

  except:
    print("The input value was wrong!!")

  return array[value]

def printWithColor(type):
  return {
    'info':'\33[92m' + 'Success: ' + '\x1b[0m',
    'added':'\33[94m' + 'Added: ' + '\x1b[0m',
    'error':'\33[91m' + 'Error: ' + '\x1b[0m',
  }.get(type, '\33[97m' + 'Info: ' + '\x1b[0m') 

def getStandardNameFromCsv(pathFile):
  lines = open(str(pathFile),'r').read()
  line=lines[0:lines.find("_||_\n")]
  line=line.replace("\xef","")
  line=line.replace("\xbb","")
  line=line.replace("\xbf","")
  line=line.replace("\n","")
  line=line.replace("\r","")
  data=list()
  while(line.find("|")!=-1):
    data.append(line[0:line.find("|")])
    line=line[line.find("|")+1:]
  data.append(line[0:])

  return data[2]

def readCsvFile(pathFile):
  data=list()
  lines = open(pathFile,'r').read()
  while(lines.find("_||_\n")!=-1):
    dataLine=list()
    line=lines[0:lines.find("_||_\n")]
    line=line.replace("\xef","")
    line=line.replace("\xbb","")
    line=line.replace("\xbf","")
    line=line.replace("\n","")
    line=line.replace("\r","")

    while(line.find("|")!=-1):
      dataLine.append(line[0:line.find("|")])
      line=line[line.find("|")+1:]
    dataLine.append(line[0:])
    data.append(dataLine)

    lines=lines[lines.find("_||_\n")+5:]

  return data

def getPath(path):
  newPath=home
  newPath=newPath.replace("src",path)
  newPath=newPath.replace("bashScripts",path)
  return newPath

def exportLib2XML(xmlFileName, rootObj):
     # We open the xml file and add the first lines of the project    
    xmlFile = open(str(xmlFileName),'w', encoding="utf8")
    xmlFile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    text="<!-- Copyright (c) 2012-%s Continuum Security.  All rights reserved.\nThe content of this library is the property of Continuum Security SL and may only be used in whole or in part with a valid license for IriusRisk. -->\n" %datetime.datetime.now().year
    xmlFile.write(text)
    rootTag = 'project'
    rootObj.export(xmlFile, 0, name_=rootTag, namespacedef_='', pretty_print=True)
    print('Generated XML file -> ', xmlFileName)

def sortFile():
  file = open(home+"/standard_list_output_final.txt",'r')
  data=file.read()
  file.close()
  array=[]
  while data.find("\n")!=-1:
    array.append(data[0:data.find("\n")])
    data=data[data.find("\n")+1:]


  array.sort()
  last=""
  written=""

  for i in array:
    if(i!=last):
      written+=i+"\n"
    last=i


  file_out = open(home+"/standard_list_output_final_sorted.txt",'w')
  file_out.write(written)
  file_out.close()


def isExcelFile(filename):
  return filename.endswith('.xls') or filename.endswith('xlsx')

def isXmlFile(filename):
  return filename.endswith('.xml')