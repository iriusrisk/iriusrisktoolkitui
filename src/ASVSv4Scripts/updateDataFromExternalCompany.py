import os
import sample_lib as sl
from pathlib import Path
import logging
import datetime

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

def main():
  path_base = Path.cwd() / "libraries" / "CS-Default.xml"
  path_new = Path.cwd() / "inputFiles" / "CS-Default-new.xml"

  data_new = sl.parse(str(path_new), silence=True)
  components_new = data_new.get_components().get_component()
  
  print('Input XML file -> ', str(path_new))
  data_old = sl.parse(str(path_base), silence=True)
  components_old =data_old.get_components().get_component()
  for component_old in components_old:
    for component_new in components_new:
      if component_new.get_ref() == component_old.get_ref():
        component_old.set_name(component_new.get_name())
        component_old.set_desc(component_new.get_desc())
        logger.info("Component '%s' was updated."%component_old.get_ref())
        for control_old in component_old.get_controls().get_control():
          for control_new in component_new.get_controls().get_control():
            if control_old.get_ref() == control_new.get_ref():
              control_old.set_name(control_new.get_name())
              control_old.set_desc(control_new.get_desc())
              control_old.set_test(control_new.get_test())
              logger.info("Control '%s' was updated."%control_old.get_ref())
        for weakness_old in component_old.get_weaknesses().get_weakness():
          for weakness_new in component_new.get_weaknesses().get_weakness():
            if weakness_old.get_ref() == weakness_new.get_ref():
              weakness_old.set_name(weakness_new.get_name())
              weakness_old.set_desc(weakness_new.get_desc())
              logger.info("Weakness '%s' was updated."%weakness_old.get_ref())
        for usecase_old in component_old.get_usecases().get_usecase():
          for usecase_new in component_new.get_usecases().get_usecase():
            if usecase_old.get_ref() == usecase_new.get_ref():
              usecase_old.set_name(usecase_new.get_name())
              usecase_old.set_desc(usecase_new.get_desc())
              logger.info("Use Case '%s' was updated."%usecase_old.get_ref())
              for threat_old in usecase_old.get_threats().get_threat():
                for threat_new in usecase_new.get_threats().get_threat():
                  if threat_old.get_ref() == threat_new.get_ref():
                    threat_old.set_name(threat_new.get_name())
                    threat_old.set_desc(threat_new.get_desc())
                    logger.info("Threat '%s' was updated."%threat_old.get_ref())

  exportLib2XML(path_base, data_old)

if __name__ == '__main__':
  main()