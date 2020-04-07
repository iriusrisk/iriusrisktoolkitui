import os
import sys
from lxml import etree, objectify
from pathlib import Path
import src.sample_lib as sl
import pandas as pd
home=os.getcwd()
from src.generateChangeLogFromVersions import createTitleHtmlFile, writeToHtml
import logging
logging.basicConfig(filename="logFile.log", 
                    format= '%(asctime)s  %(levelname)-10s %(message)s', 
                    datefmt =  "%Y-%m-%d-%H-%M-%S", 
                    filemode='w') 
  
#Creating an object 
logger=logging.getLogger() 
  
#Setting the threshold of logger to INFO 
logger.setLevel(logging.INFO) 

def getControlsList(pathFile, controlsList):
    root=sl.parse(str(Path.cwd().parents[0] / "libraries" / pathFile), silence=True)
    components=root.get_components()
    supportedStandards=root.get_supportedStandards()

    for component in components.get_component():
        controls=component.get_controls()
        for control in controls.get_control():
            controlName=control.get_name()
            controlRef=control.get_ref()
            controlDesc=control.get_desc()
            standards=control.get_standards().get_standard()
            controlStandardName=""
            controlStandardRef=""
            if len(standards)>0:                                         
                for standard in standards:
                    for supportedStandard in supportedStandards.get_supportedStandard():
                        if standard.get_supportedStandardRef() == supportedStandard.get_ref():
                            controlStandardName=supportedStandard.get_name()
                            controlStandardRef=standard.get_ref()
                            controlsList.append([controlName, controlRef, controlDesc, controlStandardName, controlStandardRef])

    return controlsList

def controlsByStantard(controls, standardName):
    controlStandard=list()
    for control in controls:
        if control[3] == standardName:
            controlStandard.append(control)
    controlStandard=sorted(controlStandard,key=lambda x: x[4])

    uniqueControls=list()
    for c in controlStandard:
        found = False
        for u in uniqueControls:
            if c == u:
                found=True
                
        if found == False:
            uniqueControls.append(c)

    return uniqueControls

def createCardBodyControl(description, card, parent, num):
    root='#%s'%parent
    carddivbody=etree.Element("div")
    carddivbody.set('id', 'collapse'+str(num))
    carddivbody.set('class', 'collapse')
    carddivbody.set('aria-labelledby', 'heading'+str(num))
    carddivbody.set('data-parent', root)
    
    cardbody=etree.Element("div")
    cardbody.set("class", "card-body")
    if description != '':
        parser = etree.HTMLParser()
        desc=etree.fromstring(description, parser)
        cardbody.append(desc)    
    
    carddivbody.append(cardbody)
    card.append(carddivbody)
    return card

def createCardHeaderControl(title, num):
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
    

    card.set("class", "card border-success")
    cardheader.set("class", "card-header")
    button.set('class', 'btn btn-light btn-group-toggle')

    
    h5.append(button)
    cardheader.append(h5)
    button.text=title
    card.append(cardheader) 
    return card

def createCardControls(dataFrame, cardBody, num):
    parent="parent%i"%num
    parentCard=etree.Element("div")
    parentCard.set("class", "accordion")
    parentCard.set("id",parent)
    for index, row in dataFrame.iterrows():
        num=num+1
        title="Countermeasure: %s [%s]"%(row['Control Name'], row['Control Id'])
        description= row['Control Desc']
        card=createCardHeaderControl(title, num)
        card=createCardBodyControl(description, card, parent, num)
        parentCard.append(card)
    cardBody.append(parentCard)
    return cardBody, num


def createCardBody(dataFrame, card, standardRef, num):
    dataFrame=dataFrame.loc[dataFrame['Standard Ref'] == standardRef]
    carddivbody=etree.Element("div")
    carddivbody.set('id', 'collapse'+str(num))
    carddivbody.set('class', 'collapse')
    carddivbody.set('aria-labelledby', 'heading'+str(num))
    carddivbody.set('data-parent', '#accordion')
    
    cardbody=etree.Element("div")
    cardbody.set("class", "card-body")

    cardbody,num=createCardControls(dataFrame, cardbody, num)
    
    carddivbody.append(cardbody)
    card.append(carddivbody)
    return card, num

def createCardHeader(standardRef, num):
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
    

    card.set("class", "card border")
    cardheader.set("class", "card-header")
    button.set('class', 'btn btn-light btn-group-toggle')

    
    h5.append(button)
    cardheader.append(h5)
    button.text="Requirement: %s" %(standardRef)
    card.append(cardheader) 
    return card

def sortArray(array):
    arraySorted = list()
    result=list()
    for i in array:
        i=str(i)
        if len(i[i.find(".")+1:])==1:
            arraySorted.append(float(i[0:i.find(".")+1]+"0"+i[-1]))
        else:
            arraySorted.append(float(i))
    arraySorted.sort(key=float)
    for i in arraySorted:
        i=str(i)
        if i[i.find(".")+1] == "0":
            result.append(i[0:i.find(".")+1]+i[i.find(".")+2:])
        if len(i[i.find(".")+1:]) == 1:
            result.append(i+"0")
        if i[i.find(".")+1] != "0" and len(i[i.find(".")+1:]) != 1:
            result.append(i)
    return result

def checkOnlyNumber(array):
    number=True
    for i in array:
        if not i.isdigit():
            number=False
    return number

def createCardsForRequirements(standards, standardsInfo, dataFrame, accordion, body):
    num=0
    if checkOnlyNumber(standards):
        standards=sortArray(standards)
    else:
        standards.sort()

    for standard in standards:
        num=num+1
        titleReq=""
        row=standardsInfo.loc[standardsInfo['Ref'] == standard]
        if len(row['Req.'].values) != 0:
            standardTitle = "%s [%s]"%(row['Req.'].values[0], standard)
        else:
            standardTitle = "%s"%(standard)
            logger.info("ERROR: The requirement '%s' wasn't found."%(standard))

        card=createCardHeader(standardTitle, num)  
        card, num=createCardBody(dataFrame, card, standard, num)
        accordion.append(card)
        body.append(accordion)
    return body
    
def generateHtml(standards, standardName, controls, libraryName):
    base_html_path=Path.cwd() / "src" / "resources" / "changelog_base_html.html"
    parser = etree.HTMLParser()
    file=etree.parse(str(base_html_path), parser)
    root=file.getroot()
    body=root.find("body")

    standardRefs=list()
    for control in controls:
        if not control[4] in standardRefs:
            standardRefs.append(control[4])
    
    dataFrame=pd.DataFrame(controls, columns=['Control Name', 'Control Id', 'Control Desc', 'Standard Name', 'Standard Ref'])
    accordion=createTitleHtmlFile(title="Standard '%s' from the library '%s'"%(standardName, libraryName), body=body)  
    
    createCardsForRequirements(standardRefs, standards, dataFrame, accordion, body)
    
    outFile_path=Path.cwd() / "outFiles" / "generatedHtml" / str(standardName.replace("/","_").replace(":","_").replace(" ","_")+".html")    
    root.find("head").find("title").text ="Standard %s from the library %s"%(standardName, libraryName)
    writeToHtml(outFile_path, file.getroot())
    return outFile_path

def generateHtmlFromLibrariesAndStandard(standard_path, arrayLibrariesPaths):
    controls=list()
    librariesNames=""
    std=pd.read_csv(standard_path, sep='|')
    std=pd.DataFrame(std.values, columns=['Category', 'Ref', 'Req.', 'Included'])   
    
    
    standardName=std['Ref'][0]
    standardRef=std['Category'][0]
    standards=std.iloc[1:]
    for lib_path in arrayLibrariesPaths:
        librariesNames+=lib_path.name.replace(".xml","")+", "
        root=sl.parse(str(lib_path), silence=True)        
        controls=getControlsList(lib_path,controls)
    controlsbyStandard=controlsByStantard(controls, standardName)
    librariesNames=librariesNames[0:-2]
    outputPath = generateHtml(standards, standardName, controlsbyStandard, librariesNames)
    return "Html file for the standard %s was generated in the path '%s'."%(standard_path.name, outputPath), outputPath
    