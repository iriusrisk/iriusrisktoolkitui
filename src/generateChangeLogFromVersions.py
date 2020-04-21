from pathlib import Path
import os
import src.sample_lib as sl
import pandas as pd
from lxml import etree
import logging
from src.libraryDetails import readInfoFromXml

#Create and configure logger 
#filemode = 'w' that will change the mode of operation from "append" to "write" and will overwrite the file every time we run our application
logging.basicConfig(filename="logFile.log", 
                    format= '%(asctime)s  %(levelname)-10s %(message)s', 
                    datefmt =  "%Y-%m-%d-%H-%M-%S", 
                    filemode='w') 
  
#Creating an object 
logger=logging.getLogger() 
  
#Setting the threshold of logger to INFO 
logger.setLevel(logging.INFO) 

EDITED = "Edited"
DELETED = "Deleted"
NEW = "New"
DATATYPES = ['Component definition','Category component','Supported standard', 'Rule', 'Risk pattern','Use case', 'Threat',  'Weakness', 'Countermeasure']

def getAllDataFromRiskPattern(riskPattern):
  threats=list()
  useCases=list()
  weaknesses=list()
  controls=list()
  
  contls=riskPattern.get_controls().get_control()
  for contl in contls:
    controls.append(contl)
  weaks=riskPattern.get_weaknesses().get_weakness()
  for weak in weaks:
    weaknesses.append(weak)
  uses=riskPattern.get_usecases().get_usecase()
  for use in uses:
    useCases.append(use)
    thrs=use.get_threats().get_threat()
    for thr in thrs:
      threats.append(thr)

  return useCases, threats, weaknesses, controls

def getAllDataFromLibrary(lib_path):
  root=sl.parse(str(lib_path), silence=True)
  componentDefinitions=root.get_componentDefinitions().get_componentDefinition()
  categoryComponents=root.get_categoryComponents().get_categoryComponent()
  supportedstandards=root.get_supportedStandards(). get_supportedStandard()
  riskPatterns=root.get_components().get_component()
  rules=root.get_rules().get_rule()
  threats=list()
  useCases=list()
  weaknesses=list()
  controls=list()
  for riskPattern in riskPatterns:
    contls=riskPattern.get_controls().get_control()
    for contl in contls:
      controls.append(contl)
    weaks=riskPattern.get_weaknesses().get_weakness()
    for weak in weaks:
      weaknesses.append(weak)
    uses=riskPattern.get_usecases().get_usecase()
    for use in uses:
      useCases.append(use)
      thrs=use.get_threats().get_threat()
      for thr in thrs:
        threats.append(thr)
  
  return componentDefinitions, categoryComponents, supportedstandards, rules, riskPatterns

def compareLoopRefAndName(data, last_data, array_attributes, typeData, library, array):
  for i in data:
    for j in last_data:
      if i.get_ref() == j.get_ref() and i.get_name() == j.get_name():
        array=compare(i, j, array_attributes, typeData, library, array)
  array=findNewObjectsByRef(data, last_data, typeData, library, array)
  array=findRemovedObjectsByRef(data, last_data, typeData, library, array)

  return array

def removeDuplicates(array):
  uniques=list()
  for i in array:
    if not i in uniques:
      uniques.append(i)
  return uniques
def compareLoop(data, last_data, array_attributes, typeData, library, array):
  
  for i in data:
    for j in last_data:
      if i.get_ref() == j.get_ref():
        array=compare(i, j, array_attributes, typeData, library, array)
  array=findNewObjectsByRef(data, last_data, typeData, library, array)
  array=findRemovedObjectsByRef(data, last_data, typeData, library, array)

  array=removeDuplicates(array)
  return array

def findNewObjectsByRef(data, last_data, typeData, library, array):
  for i in data:
    found=False
    for j in last_data:
      if i.get_ref() == j.get_ref():
        found=True
    if not found:
      array.append([library, typeData, NEW, "%s [%s]"%(i.get_name(), i.get_ref()), ""])

  return array



def findRemovedObjectsByRef(data, last_data, typeData, library, array):
  for i in last_data:
    found=False
    for j in data:
      if i.get_ref() == j.get_ref():
        found=True
    if not found:
      array.append([library, typeData, DELETED, "%s [%s]"%(i.get_name(), i.get_ref()), ""])

  return array


def findNewObjectsByName(data, last_data, typeData, library, array):
  for i in data:
    found=False
    for j in last_data:
      if i.get_name() == j.get_name():
        found=True
    if not found:
      array.append([library, typeData, NEW, i.get_name(), ""])

  return array



def findRemovedObjectsByName(data, last_data, typeData, library, array):
  for i in last_data:
    found=False
    for j in data:
      if i.get_name() == j.get_name():
        found=True
    if not found:
      array.append([library, typeData, DELETED, i.get_name(), ""])

  return array

def getReferencesFromItem(item):
  refs=list()
  for reference in item.get_references().get_reference():
    refs.append(reference.get_name()+"|"+reference.get_url())
  
  refs.sort()
  return refs

def getStandardsFromItem(item):
  standards=list()
  for standard in item.get_standards().get_standard():
    standards.append(standard.get_supportedStandardRef()+"|"+standard.get_ref())
  
  standards.sort()
  return standards

def getListOfThreatMitigation(item):
  mitigationControls=list()
  for control in item.get_controls().get_control():
    mitigationControls.append(control.get_ref()+"|"+str(control.get_mitigation()))
  
  mitigationControls.sort()
  return mitigationControls

def getImplementationsFromItem(item):
  implementations=list()
  for implementation in item.get_implementations().get_implementation():
    implementations.append(implementation.get_platform()+"|"+implementation.get_desc())
  
  implementations.sort()
  return implementations

def getAttributeFromItem(item, attribute):
  if attribute == 'name': return item.get_name()
  if attribute == 'description': return item.get_desc()
  if attribute == 'module': return item.get_module()
  if attribute == 'generatedByGui': return item.get_generatedByGui()
  if attribute == 'condition': return item.get_condition()
  if attribute == 'action': return item.get_action()
  if attribute == 'categoryRef': return item.get_categoryRef()
  if attribute == 'references': return getReferencesFromItem(item)
  if attribute == 'testReferences': return getReferencesFromItem(item.get_test())
  if attribute == 'testSteps': return item.get_test().get_steps()
  if attribute == 'state': return item.get_state()
  if attribute == 'implementations': return getImplementationsFromItem(item)
  if attribute == 'standards': return getStandardsFromItem(item)
  if attribute == 'testResult': return item.get_test().get_source().get_result()
  if attribute == 'confidentiality': return item.get_riskRating().get_confidentiality()
  if attribute == 'integrity': return item.get_riskRating().get_integrity()
  if attribute == 'availability': return item.get_riskRating().get_availability()
  if attribute == 'easeOfExploitation': return item.get_riskRating().get_easeOfExploitation()
  if attribute == 'threatMitigation': return getListOfThreatMitigation(item)
  

def compare(item, last_item, array_attributes, typeData, library, array):
  reasons=list()
  modified=False
  for i in array_attributes:
    if getAttributeFromItem(item, i) != getAttributeFromItem(last_item, i): 
      modified=True
      reasons.append(i)

  if typeData == 'Rule' and modified:
    array.append([library, typeData, EDITED, item.get_name(), reasons])
  if typeData != 'Rule' and modified:
    array.append([library, typeData, EDITED, "%s [%s]"%(item.get_name(), item.get_ref()), reasons])
  
  return array

    


def compareRules(rules, last_rules, library, array):
  typeData="Rule"
  array=findNewObjectsByName(rules, last_rules, typeData, library, array)
  array=findRemovedObjectsByName(rules, last_rules, typeData, library, array)

  array_attributes=['module', 'generatedByGui' ]

  for i in rules:
    for j in last_rules:
      if i.get_name() == j.get_name():
        array=compare(i, j, array_attributes, typeData, library, array)

  return array
      

def compareLibs(currentLibPath, beforeLibPath, lib, array):
  
  componentDefinitions, categoryComponents, supportedstandards, rules, riskPatterns = getAllDataFromLibrary(currentLibPath)

  last_componentDefinitions, last_categoryComponents, last_supportedstandards, last_rules, last_riskPatterns = getAllDataFromLibrary(beforeLibPath)


  for riskPattern in riskPatterns:
    for last_riskPattern in last_riskPatterns:
      if riskPattern.get_ref() == last_riskPattern.get_ref():
        useCases, threats, weaknesses, countermeasures = getAllDataFromRiskPattern(riskPattern)
        last_useCases, last_threats, last_weaknesses, last_countermeasures = getAllDataFromRiskPattern(last_riskPattern)
        array=compareLoop(useCases, last_useCases, ['name', 'description'] , 'Use case', lib, array)
        
        array=compareLoopRefAndName(threats, last_threats, ['name', 'description', 'references', 'state', 'confidentiality', 'availability', 'easeOfExploitation', 'integrity', 'threatMitigation'] , 'Threat', lib, array)
        array=compareLoopRefAndName(weaknesses, last_weaknesses, ['name', 'description', 'testReferences', 'state', 'testResult', 'testSteps'] , 'Weakness', lib, array)
        array=compareLoopRefAndName(countermeasures, last_countermeasures, ['name', 'description', 'references', 'standards', 'state', 'implementations', 'testResult', 'testSteps'] , 'Countermeasure', lib, array)
  
  logger.info("Info from the risk patterns was compared")
  
  
  array=compareLoop(componentDefinitions, last_componentDefinitions, ['name', 'description', 'categoryRef'], 'Component definition', lib, array)
  array=compareLoop(categoryComponents, last_categoryComponents, ['name'], 'Category component', lib, array)
  array=compareLoop(supportedstandards, last_supportedstandards, ['name'] , 'Supported standard', lib, array)
  array=compareRules(rules, last_rules, lib, array)
  array=compareLoop(riskPatterns, last_riskPatterns, ['name', 'description'] , 'Risk pattern', lib, array)
  logger.info("Info from the project was compared")
  array=removeDuplicates(array)
  
  return array


def createDataTypeCard(dataType, array):
  divElement=etree.Element("div")
  bElement=etree.Element("b")
  if dataType[0] == EDITED:
    bElement.set("style","color:orange")
  if dataType[0] == NEW:
    bElement.set("style","color:green") 
  if dataType[0] == DELETED:
    bElement.set("style","color:red") 
  bElement.text=dataType[0][0:1]
  divElement.append(bElement)
  emElement=etree.Element("em")
  emElement.text=" %s" %dataType[1]
  divElement.append(emElement)
  if dataType[2] != "": #Reason
    reasonElement=etree.Element("em")
    reasonElement.set("style", "color:gray")
    reason=""
    for j in dataType[2]:
      reason+="%s, "%j
    reason=reason[:-2]
    reasonElement.text="  Changes in: %s" %reason
    divElement.append(reasonElement)
  array.append(divElement)

  return array

def createCardDataType(dataType):
  cardDataType=etree.Element("div")
  cardDataType.set("class", "card")
  cardDataTypeheader=etree.Element("h5")
  cardDataTypeheader.set("class", "card-header")
  cardDataTypeheader.text="%s" % (dataType)
  cardDataType.append(cardDataTypeheader)

  return cardDataType

def createCardBodyModified(dataFrame, action, card, library, num):
  dataFrame=dataFrame.loc[dataFrame['Library'] == library]
  carddivbody=etree.Element("div")
  carddivbody.set('id', 'collapse'+str(num))
  carddivbody.set('class', 'collapse')
  carddivbody.set('aria-labelledby', 'heading'+str(num))
  carddivbody.set('data-parent', '#accordion')
  if action == EDITED:
      cardbody=etree.Element("div")
      cardbody.set("class", "card-body")

      for datatype in DATATYPES:
        dataType_data=dataFrame.loc[dataFrame['Data type']==datatype, ['Action', 'Name', 'Reason']].values
        if len(dataType_data) >0:
          cardDataType=createCardDataType(datatype)
          cardDataTypebody=etree.Element("div")
          cardDataTypebody.set("class", "card-body")
          for i in dataType_data:
            cardDataTypebody=createDataTypeCard(i, cardDataTypebody)           
          
          cardDataType.append(cardDataTypebody)
          cardbody.append(cardDataType)      
      
      carddivbody.append(cardbody)
      card.append(carddivbody)
  return card

def createTitleHtmlFile(title, body):
  h1Element=etree.Element("h1")
  h1Element.text=title
  h1Element.set("style","justify-content: center;text-align: center;font-weight: bold;")

  body.append(h1Element)
  accordion=etree.Element("div")
  accordion.set("id","accordion") 

  return accordion

def writeToHtml(path, data):
  data = etree.tostring(data, pretty_print=True, method="html", encoding='unicode')
  fileOutput=open(str(path), 'w')
  fileOutput.write(data)
  fileOutput.close()

def getActionFromLibrary(dataFrame, library):
  values=dataFrame.loc[dataFrame['Library']==library, ['Library', 'Data type', 'Action', 'Name', 'Reason']]
  action=values.loc[values['Data type']=="Library", ['Action']].values    
  if len(action) == 0:
    action="No actions in "
  else:
    action=action[0][0]
  return action

def createCardHeader(library, action, num):
  card=etree.Element("div")
  cardheader=etree.Element("div")
  cardheader.set('id', 'heading'+str(num))
  h5=etree.Element("h5")
  h5.set("class", "mb-0")

  button=etree.Element("button")
  
  button.set('data-toggle', 'collapse')
  button.set('data-target', '#collapse'+str(num))
  button.set('aria-expanded', 'false')
  button.set('aria-controls', 'collapse'+str(num))
  
  if action == EDITED:
    card.set("class", "card border-warning")
    cardheader.set("class", "card-header text-white bg-warning")
    button.set('class', 'btn btn-warning btn-group-toggle text-white ')
  if action == NEW:
    card.set("class", "card border-success")
    cardheader.set("class", "card-header text-white bg-success")
    button.set('class', 'btn btn-success btn-group-toggle text-white ')
  if action != EDITED and action != NEW:
    card.set("class", "card border-light")
    cardheader.set("class", "card-header")
    button.set('class', 'btn btn-light')
 
  h5.append(button)
  cardheader.append(h5)
  button.text="%s library: %s" % (action, library)
  card.append(cardheader) 
  return card

def createCardsForAllLibraries(dataFrame, libraries, accordion, body):
  num=0
  for library in libraries:
    num=num+1
    action=getActionFromLibrary(dataFrame, library)
    card=createCardHeader(library, action, num)  
    card=createCardBodyModified(dataFrame, action, card, library, num)
    accordion.append(card)
    body.append(accordion)
  return body

def generateHtmlForChangeLog(dataFrame, libraries, outFile_path):
  base_html_path=Path.cwd() / "src" / "resources" / "changelog_base_html.html"
  parser = etree.HTMLParser()
  file=etree.parse(str(base_html_path), parser)
  root=file.getroot()
  body=root.find("body")

  accordion=createTitleHtmlFile(title="Change log", body=body)  
  
  createCardsForAllLibraries(dataFrame, libraries, accordion, body)

  writeToHtml(outFile_path, file.getroot())

def compareListOfLibrariesByFiles(files, outFile_path):

  array=list()
  currentLib = files[0]
  currentLib=currentLib[currentLib.rfind("/")+1:currentLib.rfind(".xml")]
  
  array=compareLibs(files[0], files[1], currentLib, array)

  dfm=pd.DataFrame(array, columns=['Library', 'Data type', 'Action', 'Name', 'Reason'])
  logger.info("DataFrame was generated with the data of the libraries")
  
  if len(dfm.loc[dfm['Library']==currentLib, ['Library']])>1:
    array.append([currentLib, 'Library', EDITED, "", ""])
  dfm=pd.DataFrame(array, columns=['Library', 'Data type', 'Action', 'Name', 'Reason'])
  result = dfm.sort_values(['Library', 'Data type', 'Action', 'Name'], ascending=[1, 1, 1, 1])
  
  librariesModifications = dfm.loc[dfm['Data type']=='Library', ['Library', 'Action']]
  text=""
  for index, row in librariesModifications.iterrows():
    action=""
    if row['Action'] == 'Edited':
      action="from both versions were compared."
    if row['Action'] == 'New':
      action="is a new library."
    if row['Action'] == 'Deleted':
      action="from the new version was deleted."
    text+="The library '%s' %s\n"%(row['Library'], action)
  generateHtmlForChangeLog(result, [currentLib], outFile_path)
  logger.info("HTML file of the Changelog was generated in the path: %s" %outFile_path)

  return text


def compareListOfLibraries(folderCurrentRelease, folderBeforeRelease, outFile_path):
  currentLibs=os.listdir(str(folderCurrentRelease))
  beforeLibs= os.listdir(str(folderBeforeRelease))

  array=list()
  for currentLib in currentLibs:
    if currentLib in beforeLibs:
      array=compareLibs(folderCurrentRelease / currentLib, folderBeforeRelease / beforeLibs[beforeLibs.index(currentLib)], currentLib, array)
    else:
      array.append([currentLib, "Library", NEW, "", ""])

  dfm=pd.DataFrame(array, columns=['Library', 'Data type', 'Action', 'Name', 'Reason'])
  logger.info("DataFrame was generated with the data of the libraries")
  for currentLib in currentLibs:
    if len(dfm.loc[dfm['Library']==currentLib, ['Library']])>1:
      array.append([currentLib, 'Library', EDITED, "", ""])
  dfm=pd.DataFrame(array, columns=['Library', 'Data type', 'Action', 'Name', 'Reason'])
  result = dfm.sort_values(['Library', 'Data type', 'Action', 'Name'], ascending=[1, 1, 1, 1])
  
  librariesModifications = dfm.loc[dfm['Data type']=='Library', ['Library', 'Action']]
  text=""
  for index, row in librariesModifications.iterrows():
    action=""
    if row['Action'] == 'Edited':
      action="from both versions were compared."
    if row['Action'] == 'New':
      action="is a new library."
    if row['Action'] == 'Deleted':
      action="from the new version was deleted."
    text+="The library '%s' %s\n"%(row['Library'], action)
  generateHtmlForChangeLog(result, currentLibs, outFile_path)
  logger.info("HTML file of the Changelog was generated in the path: %s" %outFile_path)

  return text

def getInfoFromChangeLog(files):
  results=""
  columns=['Library Name', 'Risk Pattern', '# Use Cases', '# Threats', '# Weaknesses', '# Countermeasures']
  currentData=pd.DataFrame([], columns=columns)
  oldData=pd.DataFrame([], columns=columns)
  folderCurrentRelease=Path.cwd() / "inputFiles" / "currentRelease"
  folderBeforeRelease=Path.cwd() /  "inputFiles" / "lastRelease"

  if files == []:
    libs =os.listdir(str(folderCurrentRelease))
    for lib in libs:
      if lib.endswith(".xml"):
        data=readInfoFromXml(folderCurrentRelease / lib, columns)
        currentData=currentData.append(data)
        results+="The details of the library '%s' are shown in other window.\n"%lib
      else:
        results+="Details from file '%s' is are shown, because its extension is wrong.\n"%lib
      
    libs =os.listdir(str(folderBeforeRelease))
    for lib in libs:
      if lib.endswith(".xml"):
        data=readInfoFromXml(folderBeforeRelease / lib, columns)
        oldData=oldData.append(data)
        results+="The details of the library '%s' are shown in other window.\n"%lib
      else:
        results+="Details from file '%s' are not shown, because its extension is wrong.\n"%lib

  else:
    data=readInfoFromXml(files[0], columns)
    currentData=currentData.append(data)
    results+="The details of the library from the path '%s' are shown in other window.\n"%files[0]
    data=readInfoFromXml(files[1], columns)
    oldData=oldData.append(data)

  return currentData, oldData, results


def generateChangeLog(files):
  if files == []:
    outFile_path=Path.cwd() / "outFiles" / "changeLog.html"
    folderCurrentRelease=Path.cwd() / "inputFiles" / "currentRelease"
    folderBeforeRelease=Path.cwd() /  "inputFiles" / "lastRelease"
    text=compareListOfLibraries(folderCurrentRelease, folderBeforeRelease, outFile_path)
  else:
    outFile_path=Path.cwd() / "outFiles" / "changeLog.html"
    text=compareListOfLibrariesByFiles(files, outFile_path)
  text+="--> Changelog file generated in the path: %s" %str(outFile_path)
  return text, outFile_path

