import src.sample_lib as sl
import pandas as pd
from pathlib import Path
import os

from src.mergeLibraries import exportLib2XML

import logging
logging.basicConfig(filename="logFile.log", 
                    format= '%(asctime)s  %(levelname)-10s %(message)s', 
                    datefmt =  "%Y-%m-%d-%H-%M-%S", 
                    filemode='w') 
  
#Creating an object 
logger=logging.getLogger() 
  
#Setting the threshold of logger to INFO 
logger.setLevel(logging.INFO) 

def getReferencesByControlId(controlId, dfm):
  refs=dfm[dfm['Control Id']==controlId]
  refNames=refs['Name'].values
  refUrls=refs['URL'].values
  return refNames, refUrls

def extractAllReferencesForAllControls(dfm):
  dfm=dfm.fillna("")
  data=list()
  for index, row in dfm.iterrows():
    controls=str(row['Control Id'])
    while controls.find("\n") != -1:
      controlId = controls[0:controls.find("\n")]
      controls = controls[controls.find("\n")+1:]
      data.append([row['Name'], row['URL'], controlId])
    if controls.strip() != "":
      data.append([row['Name'], row['URL'], controls])
  
  dfm = pd.DataFrame(data, columns=['Name', 'URL', 'Control Id'])
  dfm=dfm.drop_duplicates()
  return dfm

def showMappingReport(dfm, controls, fileName):
  output_path=Path.cwd() / "outFiles" / "generatedHtml" / str("MappingReferencesToControlsFor%s.html"%fileName)
  data=list()
  for index, row in dfm.iterrows():
    for control in controls:
      if control[0] == row['Control Id']:
        data.append([row['Control Id'], control[1], str("<a href='%s'>%s</a>"%(row['URL'], row['Name']))])
  
  data=pd.DataFrame(data, columns=['Control Id', 'Control Name', 'Reference'])
  
  pd.set_option('display.max_colwidth', -1)
  pd.set_option('display.max_columns', None)
  data=data.sort_values(by=['Control Id', 'Control Name','Reference'])
  data=data.drop_duplicates()
  data=data.set_index(['Control Id', 'Control Name'], append=True).swaplevel(0,2).swaplevel(0,1)
  
  data.to_html(str(output_path), escape=False, justify='center')
  return "HTML generated with the mapping between IR countermeasures and URLs in the path: %s.\n"%output_path

def addReferencesToLibrariesByExcelFile(excel_path, replaceLibs, fileName):
  results=""
  fileName=Path(fileName).name.replace(".xlsx","")
  path_libs = Path.cwd() / "libraries"
  outlibs_path= Path.cwd() / "outFiles" / "outputLibs"
  sheet_name="Mapping References"
  dfm = pd.read_excel(str(excel_path), sheet_name=sheet_name, header=0)

  dfm = extractAllReferencesForAllControls(dfm)
  dfm.sort_values(by="Control Id", inplace=True)
  dfm=dfm.drop_duplicates()
  
  controls=list()
  for lib in os.listdir(str(path_libs)):
    if lib.endswith(".xml"):
      changed=False
      root = sl.parse(str(path_libs / lib), silence=True)
      for component in root.get_components().get_component():
        for control in component.get_controls().get_control():
          found=False
          refNames, refUrls = getReferencesByControlId(control.get_ref(), dfm)
          for referenceName, referenceUrl in zip(refNames, refUrls):
            for reference in control.get_references().get_reference():
              if referenceName == reference.get_name():
                found=True
            if not found:
              control.get_references().add_reference(sl.referenceType.factory(
                name=referenceName,
                url=referenceUrl
              ))
              changed=True
          if not found:
            controls.append([control.get_ref(), control.get_name()])
          if found:
            controls.append([control.get_ref(), control.get_name()])
            

      if changed:
        if replaceLibs:
          path = path_libs / lib
        else:
          path = outlibs_path / lib
        root.set_revision(int(root.get_revision())+1)
        exportLib2XML(str(path), root)
        results+="Library '%s' generated with the new references in the path: %s.\n"%(root.get_name(), str(path))
  
  results+=showMappingReport(dfm, controls, fileName)
  return results

