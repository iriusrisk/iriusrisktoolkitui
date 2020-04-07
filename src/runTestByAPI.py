import logging
import pandas as pd
import sys
import yaml
from src.apiCalls import postProduct, runRulesByProduct, getProduct, removeProduct
from pathlib import Path
from src.mitigationValidator import libMitigationJsonTest
import time
import json
from lxml import etree
import requests
import src.sample_lib as sl

import os
home = os.getcwd()
logging.basicConfig(filename="logFile.log",
                    format='%(asctime)s  %(levelname)-10s %(message)s',
                    datefmt="%Y-%m-%d-%H-%M-%S",
                    filemode='w')

# Creating an object
logger = logging.getLogger()

# Setting the threshold of logger to INFO
logger.setLevel(logging.INFO)


def convertStringArrayToList(string):
    data = list()
    string = string.replace("[", "")
    string = string.replace("]", "")
    string = string.replace("\"", "")
    string = string.replace("'", "")
    while string.find(",") != -1:
        if string[1:string.find(",")].strip() != "":
            data.append(string[1:string.find(",")].strip())
        string = string[string.find(",")+1:]
    if string[0:].strip() != "":
        data.append(string[0:].strip())
    return data


def isErrorInList(dataList):
    empty = True
    for i in dataList:
        if i != "":
            empty = False
    return empty


def getDataByAPI(componentDefinition, answers, urlServer, apiToken):
    xml = setDataToProduct(componentDefinition, answers)
    data = runTest(urlServer, componentDefinition, apiToken, xml)
    return data


def readConfig():
  apiToken=""
  urlServer=""
  msg=""
  path=Path.home() / ".iriusrisk.yaml"
  # If the file doesn't exist, we shal create the file.
  if not os.path.exists(str(path)):
    with open(str(path), 'w') as f:
      f.write("apiToken: \nurlServer: ")
  with open(str(Path.home() / ".iriusrisk.yaml"), 'r') as f:
    data =yaml.load(f, Loader=yaml.Loader) 
  try:   
    urlServer = data['urlServer']
    apiToken = data['apiToken']
  except:
    # If the file doesn't contain the necessary parameters
    with open(str(path), 'w') as f:
      f.write("apiToken: \nurlServer: ")
    sys.exit()
  # If the parameters are empty
  if urlServer == "" or apiToken == "" or urlServer == None or apiToken == None:
    msg="Please fill the user configuration in the file: %s"%path
  else:
    if urlServer[-1] == "/":
      urlServer=urlServer[0:-1]
    # If there is any problem with the url
    if requests.get(urlServer+"/health").status_code != 200:
      msg="Error connection: there is a problem with the url: %s"%urlServer
    # If there is any problem with the api-token
    if requests.get(urlServer+"/api/v1/groups", headers={"api-token":apiToken}).status_code != 200:
      msg="Error connection: there is a problem with the api token, review your configuration file."  
  if msg != "":
    print(msg)
    sys.exit()

  return urlServer, apiToken


def runTest(urlServer, product, apiToken, file):
    postProduct(urlServer, product, apiToken, file)
    runRulesByProduct(urlServer, product, apiToken)

    data = getProduct(urlServer, product, apiToken)
    removeProduct(urlServer, product, apiToken)

    return data


def setDataToProduct(componentDefinition, answers):
    f = open(str(Path(home+"/tests/resources/inputFiles") / "baseXml.xml"), 'r')
#    answers=convertStringArrayToList(answers)
#    dataAssets=convertStringArrayToList(dataAssets)
    dataXml = etree.parse(f)
    root = dataXml.getroot()
    root.attrib["ref"] = componentDefinition
    root.attrib["name"] = componentDefinition
    for i in root:
        if i.tag == "components":
            components = i

    for component in components:
        component.attrib["ref"] = componentDefinition
        component.attrib["name"] = componentDefinition
        component.attrib["componentDefinitionRef"] = componentDefinition
        for i in component:
            if i.tag == "questions":
                questions = i
        for answer in answers:
            element = etree.Element("question", ref=answer)
            element.attrib['answer'] = 'true'
            element.attrib['manuallyModified'] = 'false'
            questions.append(element)

    fileOutputName = str(
        Path(home+"/tests/resources/inputFiles") / "importXmlFile.xml")
    fileOut = etree.ElementTree(root)
    fileOut.write(fileOutputName, pretty_print=True)
    f.close()
    return fileOutputName


def getListOfControlsByRiskPattern(libraries, server, apiToken):
  controls = list()
  logger.info("Opened libraries for the tests: %s.\n"%libraries)
  for library in libraries:
    try:
      headers = {'api-token': apiToken}      
      response = requests.get(
          server+"/api/v1/libraries/"+library, headers=headers)
      data = response.json()
      for component in data['riskPatterns']:
        for control in component['countermeasures']:
          controls.append([component['ref'], control['ref']])
    except Exception as e:
      logger.error(e)
  return controls

def getListOfControlsByRiskPatternInProduct(data):
  controls=list()
  data=data.json()
  for component in data['components']:
    for control in component['controls']:
      controls.append([component['ref'], control['ref']])
  return controls

def getRiskPatternByControl(collectionLibrary, controlRefs):
  found=list()
  dfm = pd.DataFrame(collectionLibrary, columns=['Risk Pattern Ref', 'Control Ref'])
  dfm = dfm.sort_values('Control Ref')
  for controlRef in controlRefs:
    riskPatterns=dfm[dfm['Control Ref']==controlRef]['Risk Pattern Ref'].values
    for riskPattern in riskPatterns:
      if not riskPattern in found:
        found.append(riskPattern)
  return "Not Found but posible Risk Patterns: %s"%", ".join(found)


def checkThreatMitigation(self, data, componentDefinitions):
  # Test Threat Mitigation
  result, errors = libMitigationJsonTest(data.text, componentDefinitions)    
  self.assertTrue(result, msg=errors)

def diff(first, second):
  second = set(second)
  return [item for item in first if item not in second]

def getControlsByPatterns(patterns):
  data=list()
  path_libs = Path.cwd() / "libraries"
  for lib in os.listdir(str(path_libs)):
    if lib.endswith(".xml"):
      root = sl.parse(str(path_libs / lib), silence=True)
      for component in root.get_components().get_component():
        if component.get_ref() in patterns:
          for control in component.get_controls().get_control():
            data.append([ component.get_ref(), control.get_ref()])
  data = pd.DataFrame(data, columns=['Component Id', 'Control Id'])
  data.sort_values("Control Id", inplace=True)
  return data

def checkIfRiskPatternsExists(self, data, patterns, answers):
  result=""
  patterns.sort()
  # First we verify that all countermeasures are assigned to any given risk pattern
  collectionProduct=getListOfControlsByRiskPatternInProduct(data)
  dfmPatterns = getControlsByPatterns(patterns)
  data=list()
  for controlId in collectionProduct:
    controls=dfmPatterns[dfmPatterns['Control Id']==controlId[1]]['Component Id'].values
    if len(controls) != 0:
      data.append([controlId[1], controls[0]])
    else:
      data.append([controlId[1], ""])
  dfm = pd.DataFrame(data, columns=['Control Id', 'Risk Patterns'])
  found=dfm[dfm['Risk Patterns'] != ""]['Risk Patterns'].drop_duplicates().values
  # If there is any countermeasure without any assigned risk Pattern, we throw an error and we show the posible risk patterns for the unassigned countermeasures.
  notFound=dfm[dfm['Risk Patterns'] == ""]['Control Id'].values
  if len(notFound) != 0:
    result="The following countermeasures are not mapped to Risk Pattern: %s\nAnswered questions: %s\nFound Risk Patterns: %s\n%s"%(", ".join(notFound),", ".join(answers),", ".join(found), getRiskPatternByControl(self.collectionLibraries, notFound)) 
    logger.info(result)
  self.assertEqual(result, "")
