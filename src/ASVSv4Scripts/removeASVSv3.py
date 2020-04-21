import os
from pathlib import Path
import sample_lib as sl
import datetime

import logging
logging.basicConfig(filename="logFile.log", 
                    format= '%(asctime)s  %(levelname)-10s %(message)s', 
                    datefmt =  "%Y-%m-%d-%H-%M-%S", 
                    filemode='w') 
  
#Creating an object 
logger=logging.getLogger() 
  
#Setting the threshold of logger to INFO 
logger.setLevel(logging.INFO) 


def exportLib2XML(xmlFileName, rootObj):
     # We open the xml file and add the first lines of the project    
    xmlFile = open(str(xmlFileName),'w', encoding="utf8")
    xmlFile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    text="<!-- Copyright (c) 2012-%s Continuum Security.  All rights reserved.\nThe content of this library is the property of Continuum Security SL and may only be used in whole or in part with a valid license for IriusRisk. -->\n" %datetime.datetime.now().year
    xmlFile.write(text)
    rootObj.export(outfile=xmlFile, level=0, name_='project', namespacedef_='', pretty_print=True)
    print('Generated XML file -> ', xmlFileName)

def removeControlsAndWeaknessesFromThreats(components):
  for component in components:
    controls = list()
    weaknesses = list()
    for control in component.get_controls().get_control():
      controls.append(control.get_ref())
    for usecase in component.get_usecases().get_usecase():
      for threat in usecase.get_threats().get_threat():
        conts = sl.controlsRefType()
        for control in threat.get_controls().get_control():
          if control.get_ref() in controls:
            conts.add_control(control)
          if control.get_ref() not in controls:
            logger.info("Countermeasure '%s' was removed from the threat '%s' in the component '%s'"%(control.get_ref(), threat.get_ref(), component.get_ref()))
        threat.set_controls(conts)
        weaks = sl.weaknessesRefType()
        for weakness in threat.get_weaknesses().get_weakness():
          conts = sl.controlsRefType()
          for control in weakness.get_controls().get_control():
            if control.get_ref() in controls:
              conts.add_control(control)
            if control.get_ref() not in controls:
              logger.info("Countermeasure '%s' was removed from the weakness '%s' and threat '%s' in the component '%s'"%(control.get_ref(), weakness.get_ref(), threat.get_ref(), component.get_ref()))
          weakness.set_controls(conts)
          if len(weakness.get_controls().get_control()) > 0:
            weaks.add_weakness(weakness)
            weaknesses.append(weakness.get_ref())
        threat.set_weaknesses(weaks)
    weaks = sl.weaknessesRefType()
    for weakness in component.get_weaknesses().get_weakness():
      if weakness.get_ref() in weaknesses:
        weaks.add_weakness(weakness)
      else:
        logger.info("Weakness '%s' from component '%s' was removed."%(weakness.get_ref(), component.get_ref()))
    component.set_weaknesses(weaks)

  return components


def removeThreatsAndUsecasesWithoutControls(components):
  for component in components:
    usecases = sl.usecasesLibraryType()
    for usecase in component.get_usecases().get_usecase():
      threats = sl.threatsLibraryType()
      for threat in usecase.get_threats().get_threat():
        if len(threat.get_controls().get_control()) > 0:
          threats.add_threat(threat)
        else:
          logger.info("Threat '%s' from component '%s' was removed."%(threat.get_ref(), component.get_ref()))
      usecase.set_threats(threats)
      if len(usecase.get_threats().get_threat()) > 0:
        usecases.add_usecase(usecase)
      else:
        logger.info("Use case '%s' from component '%s' was removed."%(usecase.get_ref(), component.get_ref()))
    component.set_usecases(usecases)

  return components


def removeComponentsWithoutData(components):
  comps = sl.componentsLibraryType()
  for component in components:
    if len(component.get_controls().get_control()) > 0 or len(component.get_weaknesses().get_weakness()) > 0 or len(component.get_usecases().get_usecase()) > 0:
      comps.add_component(component)
    else:
      logger.info("Component '%s' was removed."%component.get_ref())
  return comps


def removeASVSv3FromComponents(data):
  components = data.get_components().get_component()
  for component in components:
    controls = sl.controlsLibraryType()
    for control in component.get_controls().get_control():
      asvs3=False
      asvs4=False
      
      for standard in control.get_standards().get_standard():
        if standard.get_supportedStandardRef().lower()[0:11] == 'owasp-asvs-':
          asvs3=True
        if standard.get_supportedStandardRef().lower()[0:12] == 'owasp-asvs4-':
          asvs4=True
      if not asvs3:
        controls.add_control(control)
      if asvs3 and not asvs4:
        logger.info("Countermeasure '%s' was removed from the component '%s'."%(control.get_ref(), component.get_ref()))
      if asvs3 and asvs4:
        standards = sl.standardsType()
        for standard in control.get_standards().get_standard():
          if standard.get_supportedStandardRef().lower()[0:11] != 'owasp-asvs-':
            standards.add_standard(standard)
          if standard.get_supportedStandardRef().lower()[0:11] == 'owasp-asvs-':
            logger.info("Remove the standard '%s' from the countermeasure '%s'."%(standard.get_supportedStandardRef(), control.get_ref()))
        control.set_standards(standards)
        controls.add_control(control)
    component.set_controls(controls)

  #remove Controls and weaknesses from components
  components = removeControlsAndWeaknessesFromThreats(components)
  components = removeThreatsAndUsecasesWithoutControls(components)
  components = removeComponentsWithoutData(components)
  data.set_components(components)

  return data

def removeASVSv3FromSupportedStandards(data): 
  suppStandards = sl.supportedStandardsType()
  supportedStandards = data.get_supportedStandards().get_supportedStandard()
  for supportedStandard in supportedStandards:
    if supportedStandard.get_ref().lower()[0:11] != 'owasp-asvs-':
      suppStandards.add_supportedStandard(supportedStandard)
    else:
      logger.info("Removed the Supported Standard with ref '%s'."%supportedStandard.get_ref())
  data.set_supportedStandards(suppStandards)

  return data

def removeASVS(path_lib):
  data = sl.parse(str(path_lib), silence=True)
  data = removeASVSv3FromComponents(data)
  data = removeASVSv3FromSupportedStandards(data)

  return data






def main():
  path_libs = Path.cwd() / "libraries"
  xmlFileName = Path.cwd() / "outFiles" / "libraries"
  for lib in os.listdir(str(path_libs)):
    if lib.endswith(".xml"):
      print('Input XML file -> ', str(path_libs / lib))
      data = removeASVS(path_libs / lib)
      
      exportLib2XML(xmlFileName / lib, data)

if __name__ =='__main__':
  main()