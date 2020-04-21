import pandas as pd 
import numpy as np
from moduleReadCsv import getPath#, readCsvFileWithoutEnding
import generateHtmlStandardvsCountermeasures as sToC
from pathlib import Path
import yaml
import logging
import os
import sys

import lib2_0.genLibXLS2XML.sample_lib as supermod
import lib2_0.genLibXLS2XML.validateXML as xmlcheck

import lib2_0.genLibXLS2XML.securityContent as SecurityContent

logging.basicConfig(filename="logFile.log", 
                    format= '%(asctime)s  %(levelname)-10s %(message)s', 
                    datefmt =  "%Y-%m-%d-%H-%M-%S", 
                    filemode='w') 
  
#Creating an object 
logger=logging.getLogger() 
  
#Setting the threshold of logger to INFO 
logger.setLevel(logging.INFO) 
# We get a DataFrame of data, with the data of the selected stage.
def getDataFromExcelForIoT(stage):
          xls = pd.ExcelFile(Path(getPath("inputFiles/spreadSheetFiles/"))/'Release Strategy for IoT Controls.xlsx')
          dfm=pd.read_excel(xls, header=2,sheet_name=stage+' Controls')
          dfm_filtered=dfm.filter(items=['Compliance Applicability', 'Requirement', 'Req. No', 'IR controls mapped', 'Mapped in IriusRisk', 'New IR control needed?', 'Class 0', 'Class 1', 'Class 2', 'Class 3', 'Class 4']) 
          dfm_filtered=pd.DataFrame(dfm_filtered)   
          return dfm_filtered
# with the dataframe, we generate the HTML files for the IoT standards
def createCsvInfoStandard(dataFrame, standardNames):
          for standardName in standardNames:
                    standardName_replaced=standardName.replace(" ","-")
                    dfm_filtered=dataFrame[dataFrame[standardName.replace("IoTSF ","")]=='M']
                    dfm_filtered=dfm_filtered.filter(items=['Compliance Applicability','Req. No', 'Requirement'])
                    dfm_filtered=dfm_filtered.assign(blank="", included="x")
                            
                    standards=dfm_filtered
                    controls=sToC.getControlsData(standardName.lower().replace(" ","-"),getPath("outFiles/libraries/"))
                    sToC.generateHTML(standardName, standards, controls)
                    logger.info("Html file for the standard "+standardName+" was generated.")        
              
# We add the IoT Standards for the library
def addStandardToLibrary(rootClass, dataFrame,  standardName):        
          for index, row in dataFrame.iterrows():
                    standardRef=getattr(row, "Req. No")
                    mappedControl=getattr(row, 'IR controls mapped')
                    while(mappedControl.find("\n")!=-1):                              
                              controlRef=mappedControl[0:mappedControl.find("\n")]
                              mappedControl=mappedControl[mappedControl.find("\n")+1:]
                              addStandardToControl(rootClass, controlRef,standardRef,standardName)
                    if(mappedControl.find("\n")==-1): 
                              controlRef=mappedControl
                              addStandardToControl(rootClass, controlRef,standardRef,standardName)
          
# We assign the standard to the countermeasures        
def addStandardToControl(rootClass, controlRef, standardRef, supportedStandardRef):
          riskPatterns = rootClass.get_components()
          for riskPattern in riskPatterns.get_component():
                    controls=riskPattern.get_controls()
                    for control in controls.get_control():
                              if control.get_ref() == controlRef:
                                        standards=control.get_standards()
                                        foundStandard=False
                                        for standard in standards.get_standard():
                                                  if standard.get_supportedStandardRef() ==  supportedStandardRef and standard.get_ref() == standardRef:
                                                            foundStandard=True
                                        if foundStandard == False:      
                                                  logger.info("Applied standard %s - %s to countermeasure: %s" %(supportedStandardRef, standardRef, controlRef)  )
                                                  standardClass = supermod.standardType()
                                                  standardClass.set_ref(standardRef)
                                                  standardClass.set_supportedStandardRef(supportedStandardRef)
                                                  standards.add_standard(standardClass)
                                                  

          
# We add the IoT supported standard to the library, only when any IoT standard was mapped to any control.
def addSupportedStandard(rootClass, supportedStandardRef, supportedStandardName):
          riskPatterns = rootClass.get_components()
          foundStandard=False
          # We search in all countermeasures if at least one of them has got mapped the selected standard
          for riskPattern in riskPatterns.get_component():
                    controls=riskPattern.get_controls()
                    for control in controls.get_control():                              
                              standards=control.get_standards()
                              for standard in standards.get_standard():
                                        if standard.get_supportedStandardRef() ==  supportedStandardRef:
                                                  foundStandard=True
          # If the selected standard was found, we search if the selected standard is already in the supported standadards
          if foundStandard == True:
                    supportedStandards= rootClass.get_supportedStandards()
                    sStandardFound=False
                    for supportedStandard in supportedStandards.get_supportedStandard():
                              if supportedStandard.get_ref() == supportedStandardRef or supportedStandard.get_name() == supportedStandardName:
                                        sStandardFound = True
                    # If the selected standard is not in the supported standards, we create it and add to the them.
                    if sStandardFound == False:
                              logger.info("Supported standard added: %s." %supportedStandardName)
                              supportedStandardClass = supermod.supportedStandardType()
                              supportedStandardClass.set_ref(supportedStandardRef)
                              supportedStandardClass.set_name(supportedStandardName)
                              supportedStandards.add_supportedStandard(supportedStandardClass)

# We remove the IoT standard mapped to the countermeasures
def removeStandardFromLibrary(rootClass, standardRef):
          riskPatterns = rootClass.get_components()
          for riskPattern in riskPatterns.get_component():
                    controls=riskPattern.get_controls()
                    for control in controls.get_control():
                              standards=control.get_standards()
                              standardsClass=supermod.standardsType()
                              for standard in standards.get_standard():
                                        if standard.get_supportedStandardRef() == standardRef:
                                                  logger.info("INFO: Standard %s removed from the control %s" %(standardRef, control.get_ref()))
                                        else:
                                                  standardsClass.add_standard(standard)
                              
                              control.set_standards(standardsClass)

# We remove the IoT Supported Standard from a library
def removeSupportedStandard(rootClass, supportedStandardRef):
          supportedStandards=rootClass.get_supportedStandards()
          supportedStandardsClass=supermod.supportedStandardsType()
          for supportedStandard in supportedStandards.get_supportedStandard():
                    if supportedStandard.get_ref() == supportedStandardRef:
                              logger.info("INFO: Supported standard %s removed." %supportedStandardRef)
                    else:
                              supportedStandardsClass.add_supportedStandard(supportedStandard)
          rootClass.set_supportedStandards(supportedStandardsClass)

def convertToRef(string):
          string=string.lower()
          string=string.replace(" ","-")
          return string
# We export the rootObject to xml file
def exportLib2XML(xmlFileName, rootObj, showFilePath):
          # We open the xml file and add the first lines of the project    
          xmlFile = open(xmlFileName,'w', encoding="utf8")
          xmlFile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
          rootTag = 'project'
          rootObj.export(xmlFile, 0, name_=rootTag, namespacedef_='', pretty_print=True)
          if showFilePath: 
                    print('Generated XML file -> ' + xmlFileName)

# We generate a question to select the library to apply the standard
def selectLibraryToApplyStandard():
          libraries = os.listdir(getPath("libraries"))
          # If there is not any selected library, we do the changes into all libraries.
          text="In which library do you want to apply the IoT standards?\n"
          for library in libraries:
            if library.endswith(".xml"):
              text+="%i - %s\n"%(libraries.index(library),library)
          text+="%i - %s\n"%(len(libraries)+1,"All libraries")
          valueText=int(input(text))
          if valueText <= len(libraries):
            libraries=[libraries[valueText]]
          return libraries

# We ask if we want to remove the current mapping of the selected standard (IoT), before we apply the new mapping.
def removeStandards(libraries, standardNames):
          value = ""          
          while value != 'y' and value != 'n':
                    value=input("Do you want to remove the IoT standard from the libraries, before we add the new standard mapping (y/n)? ")
          
          if value == 'y':
                    removeStandardsFromCountermeasures(libraries, standardNames)
                    copyOutputLibrariesToMainLibraries(libraries)

# We ask about which stage of the IoT standard, we want to apply and we get the Data from the excel 
def selectStage():
          stages=['Stage 1', 'Stage 2', 'Stage 3']
          text="Select the number of the stage to apply the standard: \n"
          for stage in stages:
                    text+="%i - %s\n" %(stages.index(stage), stage)
          valueStage=99
          while valueStage<0 or valueStage > len(stages):
                    valueStage=int(input(text))
          
          selectedStage=stages[valueStage]
          dfm=getDataFromExcelForIoT(selectedStage)
          logger.info("Read Data from Excel file with the info of the mapping")
          return dfm
# We apply the standard to the selected libraries and for the selected stage.
def applyStandardToLibraries(libraries, standardNames, dataExcel):
          for library in libraries:                   
                    logger.info("Opened library %s" %library)
                    rootClass = supermod.parse(str(Path(getPath("libraries")) / library), True)   
                    
                    for standardName in standardNames:
                              addStandardToLibrary(rootClass, dataExcel[dataExcel[standardName.replace("IoTSF ","")] == 'M'], convertToRef(standardName))
                              addSupportedStandard(rootClass, convertToRef(standardName), standardName)
                    
                    exportLib2XML(str(Path(getPath("outFiles/libraries/")) / library), rootClass, True)

# We call all methods to do the IoT mapping, if a library was selected, we apply the IoT standard only for this library.
def mappingIoT():
          standardNames=["IoTSF Class 0", "IoTSF Class 1", "IoTSF Class 2", "IoTSF Class 3", "IoTSF Class 4"]
          libs=selectLibraryToApplyStandard()
          removeStandards(libs, standardNames)          
          dataExcel=selectStage()
          applyStandardToLibraries(libs, standardNames, dataExcel)
          createCsvInfoStandard(dataExcel,standardNames)
# We remove the IoT Standard from each countermeasure
def removeStandardsFromCountermeasures(libraries, standardNames):
          rootClass = supermod.libraryType()
          for lib in libraries:
                    logger.info("Opened library %s" %lib)
                    rootClass = supermod.parse(str(Path(getPath("libraries")) / lib), True) 
                    for standardName in standardNames:  
                              removeStandardFromLibrary(rootClass, convertToRef(standardName))
                              removeSupportedStandard(rootClass, convertToRef(standardName))
                    
                    exportLib2XML(str(Path(getPath("outFiles/libraries/")) / lib), rootClass, False)
# copy the xml file from the folder output to the folder libraries
def copyOutputLibrariesToMainLibraries(libraries):
          origin=Path(getPath("outFiles/libraries"))
          destination=str(Path(getPath("libraries")))          
          for library in libraries:
                    originPath=origin / library
                    os.system("cp %s %s" %(originPath, destination))
                    logger.info("INFO FILE: The file %s was copied from %s to %s." %(library, origin, destination))

def main():
          if len(sys.argv) == 1:
                    mappingIoT() 
          if len(sys.argv) != 1:
                    print("Error: More arguments than necessary!!")

if __name__ == '__main__':
          main()