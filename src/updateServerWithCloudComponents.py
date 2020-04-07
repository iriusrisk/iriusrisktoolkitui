import os
import sys
from lxml import etree
import json
import requests
import sys
import yaml
import logging

home=os.getcwd()
from pathlib import Path

from src.apiCalls import *
import src.sample_lib as sl
import src.xmlValidator as xmlcheck
import src.securityContent as SecurityContent

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


def updateCategoryComponents(rootClass, libProps):
    categoryComponents = rootClass.get_categoryComponents()
    categoryComponentClass = sl.categoryComponentType()

    componentDefinitionClass = sl.componentDefinitionType()   
    
    if 'categories' in libProps.keys():
        categories = libProps['categories']
        if categories != "":
            for category in categories:
                categoryComponentObj = categoryComponentClass.factory(name=categories[category]['name'], ref=categories[category]['ref'])
                categoryComponents.add_categoryComponent(categoryComponentObj)
                logger.info("|--> Category created: %s" % categories[category]['name'])


    
def createRiskPatternsComponentDefinition(refs):
    riskPatternsClass = sl.riskPatternsType()
    riskPatternClass = sl.riskPatternType()

    for ref in refs:
        riskPatternObj = riskPatternClass.factory(ref)
        riskPatternsClass.add_riskPattern(riskPatternObj)

    return riskPatternsClass

def updateComponentDefinitions(rootClass, libProps):
    componentDefinitions = rootClass.get_componentDefinitions()
    componentDefinitionClass = sl.componentDefinitionType()   
    
    if 'componentDefinitions' in libProps.keys():
        definitions = libProps['componentDefinitions']

        for definition in definitions:
            #Each componentDefinition can import several riskPatterns
            riskPatternsClass = createRiskPatternsComponentDefinition(definitions[definition]['riskPattern'])
            componentDefinitionObj = componentDefinitionClass.factory(
                definitions[definition]['ref'], 
                definitions[definition]['name'], 
                definitions[definition]['desc'],
                definitions[definition]['category'],
                riskPatternsClass)
            componentDefinitions.add_componentDefinition(componentDefinitionObj)
            logger.info("|--> Component definition created: %s" % definitions[definition]['name'])

def removeRules(rootClass, libProps):
    #newRootClass = sl.libraryType()
    rules = rootClass.get_rules()
    rulesClass = sl.rulesType()
    if 'rulesToRemove' in libProps.keys():
        rulesToRemove = libProps['rulesToRemove']
        for rule in rules.get_rule():
            found=False            
            for ruleToRemove in rulesToRemove:
                if rule.name in rulesToRemove[ruleToRemove]:
                    found=True                    
            if not found:
                rulesClass.add_rule(rule)
            else:
                logger.info("|--> Rule removed: %s" % rule.name)
        rootClass.set_rules(rulesClass)
def addConditions(ruleObj, libProps):
    conditionClass = sl.conditionType()
    for condition in libProps:
        condition=libProps[condition]
        condObj=conditionClass.factory(
            name=condition['name'],
            type=condition['type'],
            field=condition['field'],
            value=condition['value']
        )
        condObj.set_type(condition['type'])
        addPattern(condObj, condition['pattern']['name'], condition['pattern']['pattern'])
        ruleObj.add_condition(condObj)

def addPattern(objClass, name, pattern):
    patternClass = sl.patternType()
    patternObj = patternClass.factory(
        name=name,
        pattern=pattern
    )
    objClass.set_pattern(patternObj)

def addActions(ruleObj, libProps):
    actionClass = sl.actionType()
    for action in libProps:
        action=libProps[action]
        actionObj=actionClass.factory(
            name=action['name'],
            type=action['type'],
            project=action['project'],
            value=action['value']
        )
        actionObj.set_type(action['type'])
        addPattern(actionObj, action['pattern']['name'], action['pattern']['pattern'])
        ruleObj.add_action(actionObj)

def createRules(rootClass, libProps):
    ruleClass = sl.ruleType()
    rules = rootClass.get_rules()
    rulesClass = sl.rulesType()
    
    if 'rulesToCreate' in libProps.keys():
        rulesToCreate = libProps['rulesToCreate']  
        for rule in rulesToCreate:
            rule=rulesToCreate[rule]
            ruleObj=ruleClass.factory(
                name=rule['name'],
                module=rule['module'],
                generatedByGui=True,
                content=""
            )
            addConditions(ruleObj, rule['conditions'])
            addActions(ruleObj, rule['actions'])

            rules.add_rule(ruleObj)
            logger.info("|--> Rule created: %s" % rule['name'])
        rootClass.set_rules(rules)
        

def exportLib2XML(xmlFileName, rootObj):
     # We open the xml file and add the first lines of the project    
    xmlFile = open(xmlFileName,'w', encoding="utf8")
    xmlFile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    rootTag = 'project'
    rootObj.export(xmlFile, 0, name_=rootTag, namespacedef_='', pretty_print=True)
    print('Generated XML file -> ' + xmlFileName)

def updateLibrary(xmlFilePath, xmlFilePathDestination):
    rootClass = sl.libraryType()
    fileName=xmlFilePath[xmlFilePath.rfind("/")+1:xmlFilePath.rfind(".xml")]
    f = open(str(Path.cwd() / "src" / "resources")/'updateDemolibProperties.yaml')
    libProperties = yaml.safe_load(f)
    f.close()
    if fileName in libProperties:     
        rootClass = sl.parse(xmlFilePath, True)        
        
        logger.info("Component Definitions and Categories creation process for the library '%s' is STARTED." %fileName)
        updateCategoryComponents(rootClass, libProperties[fileName])
        updateComponentDefinitions(rootClass, libProperties[fileName])
        logger.info("Component Definitions and Categories creation process for the library '%s' is FINISHED." %fileName)            
    
        logger.info("Rules deletion process for the library '%s' is STARTED." %fileName)
        removeRules(rootClass, libProperties[fileName])
        logger.info("Rules deletion process for the library '%s' is FINISHED." %fileName)
        logger.info("Rules creation process for the library '%s' is STARTED." %fileName)
        createRules(rootClass, libProperties[fileName])
        logger.info("Rules creation process for the library '%s' is FINISHED." %fileName)                      
        exportLib2XML(xmlFilePathDestination, rootClass)
        
# We use this script to catch the arguments and run the principal method


def modifyLibraries():
    for lib in os.listdir(Path.cwd() / "libraries"):
        if lib.endswith(".xml"):
                updateLibrary(Path.cwd() / "libraries" / lib, Path.cwd() / "outFiles" / "libraries" / lib)


def removeLibraryByApi(pathLibrary, urlServer, apiToken):
        libRef=sl.parse(str(pathLibrary), silence=True).get_ref()       
        responseGet= getLibrary(urlServer, libRef, apiToken)
        if responseGet.status_code == 200:
                response=removeLibrary(urlServer, libRef, apiToken)
                if response.status_code == 204:
                        logger.info("The library %s was removed well with the status code: %s" % (libRef, response.status_code))
                else:
                        logger.error("The library %s was not removed well, the api call has got the next response: %s"  % (libRef, response.text))
        else:
                logger.error("The Get libraries call failed for the library %s and with the response: %s" % (libRef, responseGet.text))

def uploadLibraryByApi(pathLibrary, urlServer, apiToken):        
        libRef=sl.parse(str(pathLibrary), silence=True).get_ref()     
        responsePost=postLibrary(urlServer, libRef, apiToken, pathLibrary)
        if(responsePost.status_code == 201):
                text="The library %s was uploaded well.\n" % (libRef)
                logger.info(text)
                return text
        else:
                text="The library %s was not uploaded well, the api call has got the next response: %s.\n"  % (libRef, responsePost.text)
                logger.error(text)
                return text