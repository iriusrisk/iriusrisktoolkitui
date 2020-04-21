import os
home=os.getcwd()
from lxml import etree, objectify
import sys
from src.xmlValidator import xmlValidator
from pathlib import Path
import src.sample_lib as sl
import pandas as pd

from src.common import exportLib2XML
import logging

logging.basicConfig(filename="logFile.log", 
                    format= '%(asctime)s  %(levelname)-10s %(message)s', 
                    datefmt =  "%Y-%m-%d-%H-%M-%S", 
                    filemode='w') 
  
#Creating an object 
logger=logging.getLogger() 
  
#Setting the threshold of logger to INFO 
logger.setLevel(logging.INFO) 


def createStandard(supportedStandardRef, standardRef):
    standardClass = sl.standardType()
    return standardClass.factory(supportedStandardRef=supportedStandardRef,
    ref=standardRef)
    

def searchControls(library_path, supportedStandard_name, standard_file_path):
    rootObj = sl.parse(str(library_path), silence=True)
    
    supportedStandards=rootObj.get_supportedStandards()
    components=rootObj.get_components().get_component()
     

    supportedStandardCreated = False

    dfm = pd.read_csv(str(standard_file_path), sep="|")
    dfm.columns=['Standard ASVS', "Ref ASVS", "Supported Standard Name", "Supported Standard Ref", "Standard Ref"]
    
    for index, row in dfm.iterrows():
        asvs_supportedStandardRef=row.get("Standard ASVS")
        asvs_ref=str(row.get("Ref ASVS"))
        supportedStandard_name=row.get("Supported Standard Name")
        supportedStandardRef=row.get("Supported Standard Ref")
        standardRef=row.get("Standard Ref")
        for component in components:
            controls=component.get_controls().get_control()
            for control in controls:
                standards = control.get_standards()
                for standard in standards.get_standard():

                    if standard.get_supportedStandardRef()==asvs_supportedStandardRef:
                        if standard.get_ref()==asvs_ref:
                            alreadyExist=False
                            for stard in standards.get_standard():
                                if stard.get_supportedStandardRef() == supportedStandardRef and stard.get_ref() == standardRef:
                                    alreadyExist=True
                            #construir standard y añadirlo
                            if alreadyExist == False:
                                standards.add_standard(createStandard(supportedStandardRef, standardRef))
                                supportedStandardCreated=True
                            
    supportedStandardFound = False
    for supportedStandard in supportedStandards.get_supportedStandard():  
        if supportedStandard.get_ref() == supportedStandardRef:
            supportedStandardFound = True
            
    if supportedStandardFound == False and supportedStandardCreated == True:        
        supportedStandards.add_supportedStandard(sl.supportedStandardType.factory(ref=supportedStandardRef,name=supportedStandard_name))
        rootObj.set_revision(int(rootObj.get_revision())+1)  
        output_path=Path.cwd() / "outFiles" / "libraries" / library_path.name
        exportLib2XML(str(output_path), rootObj)
        text="SuportedStandard was added for the library and saved in the new created file '%s'\n"%output_path
        
    else: 
        if supportedStandardCreated == True:
            rootObj.set_revision(int(rootObj.get_revision())+1)  
            output_path=Path.cwd() / "outFiles" / "libraries" / library_path.name
            exportLib2XML(str(output_path), rootObj)
            text="SuportedStandard was updated for the library and saved in the new created file '%s'\n"%output_path
        else:
            text="SuportedStandard was not necessary to create for the library '%s'\n"%library_path.name

    print(text)
    return text

def addXmlTag(pathFile):
    openFile=open(pathFile,'r')
    data=openFile.read()
    openFile.close()
    data="<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"+data
    output=open(pathFile,'w')
    output.write(data)
    output.close()

def addStandardToLibrary(standard_path_csv, path_library, standardName):
    path_xsd=Path.cwd() / "inputFiles" / "XSD_Schema" / "library.xsd"
    if xmlValidator(path_library, path_xsd) == True:
        return searchControls(path_library, standardName, standard_path_csv)
