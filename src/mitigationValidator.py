# -*- coding: utf-8 -*-
import os
from lxml import etree
import sys
from pathlib import Path
import json
import logging
import src.sample_lib as sl

home=os.getcwd()

logging.basicConfig(filename="logFile.log", 
                    format= '%(asctime)s  %(levelname)-10s %(message)s', 
                    datefmt =  "%Y-%m-%d-%H-%M-%S", 
                    filemode='w') 
  
#Creating an object 
logger=logging.getLogger() 
  
#Setting the threshold of logger to INFO 
logger.setLevel(logging.INFO)

def libMitigationJsonTest(data, productName, exceptions):
    version = ''
    try:
      version = os.getenv('ASVS')
    except expression as identifier:
      print("The environment variable 'ASVS' is not set.")
      pass
    errors=""
    node = json.loads(data)

    components = node['components']

    totalThreats = 0
    totalCountermeasures = 0
    globalTestMitigationForLibrary = True

    for component in components:
        for usecase in component['usecases']:
        
            for threat in usecase['threats']:
              if not [component['ref'], threat['ref']] in exceptions:
                totalMitigation = 0
                controls=list()
                for weakness in threat['weaknesses']:
                    for control in weakness['controls']:
                        controls.append(control)
                for control in threat['controls']:
                    controlRef = control['ref']
                    mitigation = control['mitigation']
                    #print("Controls mitigation: " + control.attrib['mitigation'])
                    if control in controls:
                        if control['ref'] == controls[controls.index(control)]['ref']:
                            totalMitigation = totalMitigation + int(mitigation)
                    #We also check we have the same value for control ref and control mitigation under the weaknesses tree
                
                if totalMitigation != 100 and version == 3:
                  errors+="Mitigation test for threat ref: " + threat['ref'] + "-> FAILED\n"
                  globalTestMitigationForLibrary = False
                
                if totalMitigation >= 100 and totalMitigation <= 130 and version == 4:
                  errors+="Mitigation test for threat ref: " + threat['ref'] + "-> FAILED\n"
                  globalTestMitigationForLibrary = False

    return globalTestMitigationForLibrary, errors

def libMitigationTestASVSv4(lib_path, exceptions, forAsvs4=False):
  text=""
  errors=list()
  errorsIntegrity=list()
  root = sl.parse(str(lib_path), silence=True)
  components = root.get_components()
  
  libraryRef=root.get_ref()
  
  for component in components.get_component():    
    asvs4Controls = list()
    for control in component.get_controls().get_control():
      asvs4 = False
      asvs3 = False
      for standard in control.get_standards().get_standard():
        if standard.get_supportedStandardRef()[0:12] == 'owasp-asvs4-':
          asvs4 = True
        if standard.get_supportedStandardRef()[0:11].lower() == 'owasp-asvs-':
          asvs3 = True
      if asvs4:
        asvs4Controls.append(control.get_ref())
      if not asvs3 and not asvs4:
        asvs4Controls.append(control.get_ref())
    for usecase in component.get_usecases().get_usecase():
      for threat in usecase.get_threats().get_threat():
        totalMitigation = 0        
        for control in threat.get_controls().get_control():
          if control.get_ref() in asvs4Controls:
            totalMitigation = totalMitigation + int(control.get_mitigation())
            #We also check we have the same value for control ref and control mitigation under the weaknesses tree
            for weakness in threat.get_weaknesses().get_weakness():
              for contrl in weakness.get_controls().get_control():
                if control.get_ref() == contrl.get_ref() and control.get_mitigation() != contrl.get_mitigation():
                  errorsIntegrity.append(control.get_ref())
        if [component.get_ref(), threat.get_ref()] in exceptions:
          totalMitigation = 100

        if totalMitigation < 100 and totalMitigation > 0:
          print("Component Id: %s --> Threat: %s == Mitigation: %s"%(component.get_ref(), threat.get_ref(), totalMitigation))
          errors.append(threat.get_ref())
        if totalMitigation > 140:
          print("Component Id: %s --> Threat: %s == Mitigation: %s"%(component.get_ref(), threat.get_ref(), totalMitigation))
          errors.append(threat.get_ref())
  text=""
  if len(errorsIntegrity) != 0:
    text+="Threat mitigation integrity fails in the following countermeasures: %s\n"%str(errorsIntegrity).replace("[","").replace("]","")
  if len(errors) != 0:
    text+="Threat mitigation fails in the following threats: %s\n"%str(errors).replace("[","").replace("]","")
  return text

def libMitigationTestASVSv3(lib_path, exceptions, forAsvs4=False):
  text=""
  errors=list()
  errorsIntegrity=list()
  root = sl.parse(str(lib_path), silence=True)
  components = root.get_components()
  
  libraryRef=root.get_ref()
  
  for component in components.get_component():    
    asvs3Controls = list()
    for control in component.get_controls().get_control():
      asvs4 = False
      asvs3 = False
      for standard in control.get_standards().get_standard():
        if standard.get_supportedStandardRef()[0:12] == 'owasp-asvs4-':
          asvs4 = True
        if standard.get_supportedStandardRef()[0:11].lower() == 'owasp-asvs-':
          asvs3 = True
      if asvs3:
        asvs3Controls.append(control.get_ref())
      if not asvs3 and not asvs4:
        asvs3Controls.append(control.get_ref())
    for usecase in component.get_usecases().get_usecase():
      for threat in usecase.get_threats().get_threat():
        totalMitigation = 0        
        for control in threat.get_controls().get_control():
          if control.get_ref() in asvs3Controls:
            totalMitigation = totalMitigation + int(control.get_mitigation())
            #We also check we have the same value for control ref and control mitigation under the weaknesses tree
            for weakness in threat.get_weaknesses().get_weakness():
              for contrl in weakness.get_controls().get_control():
                if control.get_ref() == contrl.get_ref() and control.get_mitigation() != contrl.get_mitigation():
                  errorsIntegrity.append(control.get_ref())
        if [component.get_ref(), threat.get_ref()] in exceptions:
          totalMitigation = 100

        if totalMitigation < 100 and totalMitigation > 0:
          print("Component Id: %s --> Threat: %s == Mitigation: %s"%(component.get_ref(), threat.get_ref(), totalMitigation))
          errors.append(threat.get_ref())
        if totalMitigation > 140:
          print("Component Id: %s --> Threat: %s == Mitigation: %s"%(component.get_ref(), threat.get_ref(), totalMitigation))
          errors.append(threat.get_ref())

  text=""
  if len(errorsIntegrity) != 0:
    text+="Threat mitigation integrity fails in the following countermeasures: %s\n"%str(errorsIntegrity).replace("[","").replace("]","")
  if len(errors) != 0:
    text+="Threat mitigation fails in the following threats: %s\n"%str(errors).replace("[","").replace("]","")
  return text
  
 

def libMitigationTest(lib_path, exceptions, forAsvs4=False):
  text=""
  errors=list()
  errorsIntegrity=list()
  root = sl.parse(str(lib_path), silence=True)
  components = root.get_components()
  
  libraryRef=root.get_ref()
  
  for component in components.get_component():    
    asvs4Controls = list()
    asvs3Controls = list()
    restControls = list()
    for control in component.get_controls().get_control():
      asvs4 = False
      asvs3 = False
      for standard in control.get_standards().get_standard():
        if standard.get_supportedStandardRef()[0:11].lower() == 'owasp-asvs-':
          asvs4 = True
        if standard.get_supportedStandardRef()[0:11] == 'OWASP-ASVS-':
          asvs3 = True
      if asvs3:
        asvs3Controls.append(control.get_ref())
      if asvs4:
        asvs4Controls.append(control.get_ref())
      if not asvs3 and not asvs4:
        asvs3Controls.append(control.get_ref())
        asvs4Controls.append(control.get_ref())
    for usecase in component.get_usecases().get_usecase():
      for threat in usecase.get_threats().get_threat():
        print("Threat: %s"%threat.get_ref())
        #print(" --> ASVSv3: %s"%asvs3Controls)
        #print(" --> ASVSv4: %s"%asvs4Controls)
        totalMitigation = 0        
        for control in threat.get_controls().get_control():
          if forAsvs4 and control.get_ref() in asvs4Controls:
            print(control.get_ref())
            totalMitigation = totalMitigation + int(control.get_mitigation())
            #We also check we have the same value for control ref and control mitigation under the weaknesses tree
            for weakness in threat.get_weaknesses().get_weakness():
              for contrl in weakness.get_controls().get_control():
                if control.get_ref() == contrl.get_ref() and control.get_mitigation() != contrl.get_mitigation():
                  errorsIntegrity.append(control.get_ref())
          if not forAsvs4 and control.get_ref() in asvs3Controls:
            totalMitigation = totalMitigation + int(control.get_mitigation())
            #We also check we have the same value for control ref and control mitigation under the weaknesses tree
            for weakness in threat.get_weaknesses().get_weakness():
              for contrl in weakness.get_controls().get_control():
                if control.get_ref() == contrl.get_ref() and control.get_mitigation() != contrl.get_mitigation():
                  errorsIntegrity.append(control.get_ref())
        if [component.get_ref(), threat.get_ref()] in exceptions:
          totalMitigation = 100

        if totalMitigation != 100:
          errors.append(threat.get_ref())
  text=""
  if len(errorsIntegrity) != 0:
    text+="Threat mitigation integrity fails in the following countermeasures: %s\n"%str(errorsIntegrity).replace("[","").replace("]","")
  if len(errors) != 0:
    text+="Threat mitigation fails in the following threats: %s\n"%str(errors).replace("[","").replace("]","")
  return text
  
def main():
    path=Path.cwd() / "libraries"    
    xmlFiles=os.listdir(path)
    text="Select the number of the desired XML library to be tested against mitigations check:\n"
    for xmlFile in xmlFiles:
        text+="%i - %s\n" %(xmlFiles.index(xmlFile), xmlFile)
    value = 9999
    while value <0 or value>len(xmlFiles):
        value=int(input(text))

    xmlFilePath = path / xmlFiles[value]
    libMitigationTest(str(xmlFilePath)) 

if __name__ == '__main__':
    main()