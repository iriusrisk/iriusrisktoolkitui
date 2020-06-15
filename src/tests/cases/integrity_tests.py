import pandas as pd
import os
from pathlib import Path
import src.sample_lib as sl
import lxml.etree as etree
from bs4 import BeautifulSoup
import html
import logging
from datetime import date
logging.basicConfig(filename="logFile.log", 
                    format= '%(asctime)s  %(levelname)-10s %(message)s', 
                    datefmt =  "%Y-%m-%d-%H-%M-%S", 
                    filemode='w') 
  
#Creating an object 
logger=logging.getLogger() 
  
#Setting the threshold of logger to INFO 
logger.setLevel(logging.DEBUG) 

def checkComponentAsvs3AndAsvs4(path):
  components=list()
  controls=list()
  for lib in os.listdir(str(path)):
    if lib.endswith(".xml"):
      root=sl.parse(str(path / lib), silence=True)
      for componentDefinition in root.get_componentDefinitions().get_componentDefinition():
        for riskPattern in componentDefinition.get_riskPatterns().get_riskPattern():
          components.append([root.get_ref(), componentDefinition.get_ref(), componentDefinition.get_name(), riskPattern.get_ref()])

      for component in root.get_components().get_component():
        for control in component.get_controls().get_control():
          for standard in control.get_standards().get_standard():
            controls.append([root.get_ref(), component.get_ref(), control.get_ref(), control.get_name(), standard.get_supportedStandardRef(), standard.get_ref()])
            
  columns=['Library Id', 'Risk Pattern Id', 'Control Id', 'Control Name', 'Supported Standard Ref', 'Standard Ref']
  dfm = pd.DataFrame(controls, columns=columns)

  columnsComps = ['Library Id', 'Component Definition Id', 'Component Definition Name', 'Risk Pattern Id']
  dfmComps = pd.DataFrame(components, columns=columnsComps)

  asvs3=['OWASP-ASVS-Level-1', 'OWASP-ASVS-Level-2', 'OWASP-ASVS-Level-3']
  asvs4=['owasp-asvs4-level-1', 'owasp-asvs4-level-2', 'owasp-asvs4-level-3']

  asvs3_1=dfm[dfm['Supported Standard Ref'] == asvs3[0]]
  asvs3_2=dfm[dfm['Supported Standard Ref'] == asvs3[1]]
  asvs3_3=dfm[dfm['Supported Standard Ref'] == asvs3[2]]

  riskPattern3=asvs3_1.append(asvs3_2).append(asvs3_3)
  riskPattern3 = riskPattern3.sort_values(['Risk Pattern Id', 'Control Id']).drop_duplicates(['Risk Pattern Id', 'Control Id'])

  asvs4_1=dfm[dfm['Supported Standard Ref'] == asvs4[0]]
  asvs4_2=dfm[dfm['Supported Standard Ref'] == asvs4[1]]
  asvs4_3=dfm[dfm['Supported Standard Ref'] == asvs4[2]]

  riskPattern4 = asvs4_1.append(asvs4_2).append(asvs4_3)
  riskPattern4 = riskPattern4.sort_values(['Risk Pattern Id', 'Control Id']).drop_duplicates(['Risk Pattern Id', 'Control Id'])

  compAsvs3=pd.DataFrame([], columns=columns+['Component Definition Id'])
  compAsvs4=pd.DataFrame([], columns=columns+['Component Definition Id'])
  for componentDefinition in dfmComps.sort_values(['Component Definition Id']).drop_duplicates(['Component Definition Id'])['Component Definition Id'].values.tolist():
    riskPatterns = dfmComps[dfmComps['Component Definition Id'] == componentDefinition]['Risk Pattern Id'].values.tolist()

    for riskPattern in riskPatterns:
      
      temp=riskPattern3[riskPattern3['Risk Pattern Id'] == riskPattern]
      temp.insert(6, 'Component Definition Id', [componentDefinition] * len(temp))
     
      compAsvs3=compAsvs3.append(temp)

      temp=riskPattern4[riskPattern4['Risk Pattern Id'] == riskPattern]
      temp.insert(6, 'Component Definition Id', [componentDefinition] * len(temp))
     
      compAsvs4=compAsvs4.append(temp)
  

  riskPattern3NotIn4=list()
  for value in compAsvs3[['Component Definition Id']].drop_duplicates(['Component Definition Id']).values:
    if not value in compAsvs4[['Component Definition Id']].drop_duplicates(['Component Definition Id']).values:
      if not value[0] in riskPattern3NotIn4:
        riskPattern3NotIn4.append("'%s'"%value[0])

  riskPattern4NotIn3=list()
  for value in compAsvs4[['Component Definition Id']].drop_duplicates(['Component Definition Id']).values:
    if not value in compAsvs3[['Component Definition Id']].drop_duplicates(['Component Definition Id']).values:
      if not value in riskPattern4NotIn3:
        riskPattern4NotIn3.append("'%s'"%value[0])

  errors=""
  if len(riskPattern3NotIn4) != 0:
    errors+="The following Component Definitions are in the ASVS v3 but not in the v4: %s.\n\n"%str(", ".join(riskPattern3NotIn4))
  if len(riskPattern4NotIn3) != 0:
    errors+="The following Component Definitions are in the ASVS v4 but not in the v3: %s.\n\n"%str(", ".join(riskPattern4NotIn3))
  

  return errors


def checkRiskPatternAsvs3AndAsvs4(path):
  controls=list()
  for lib in os.listdir(str(path)):
    if lib.endswith(".xml"):
      root=sl.parse(str(path / lib), silence=True)
      for component in root.get_components().get_component():
        for control in component.get_controls().get_control():
          for standard in control.get_standards().get_standard():
            controls.append([root.get_ref(), component.get_ref(), control.get_ref(), control.get_name(), standard.get_supportedStandardRef(), standard.get_ref()])
            
  columns=['Library Id', 'Risk Pattern Id', 'Control Id', 'Control Name', 'Supported Standard Ref', 'Standard Ref']
  dfm = pd.DataFrame(controls, columns=columns)

  asvs3=['OWASP-ASVS-Level-1', 'OWASP-ASVS-Level-2', 'OWASP-ASVS-Level-3']
  asvs4=['owasp-asvs4-level-1', 'owasp-asvs4-level-2', 'owasp-asvs4-level-3']

  asvs3_1=dfm[dfm['Supported Standard Ref'] == asvs3[0]]
  asvs3_2=dfm[dfm['Supported Standard Ref'] == asvs3[1]]
  asvs3_3=dfm[dfm['Supported Standard Ref'] == asvs3[2]]

  riskPattern3=asvs3_1.append(asvs3_2).append(asvs3_3)
  riskPattern3 = riskPattern3.sort_values(['Risk Pattern Id', 'Control Id']).drop_duplicates(['Risk Pattern Id', 'Control Id'])

  asvs4_1=dfm[dfm['Supported Standard Ref'] == asvs4[0]]
  asvs4_2=dfm[dfm['Supported Standard Ref'] == asvs4[1]]
  asvs4_3=dfm[dfm['Supported Standard Ref'] == asvs4[2]]

  riskPattern4 = asvs4_1.append(asvs4_2).append(asvs4_3)
  riskPattern4 = riskPattern4.sort_values(['Risk Pattern Id', 'Control Id']).drop_duplicates(['Risk Pattern Id', 'Control Id'])

  riskPattern3NotIn4=list()
  for value in riskPattern3[['Risk Pattern Id']].values:
    if not value in riskPattern4[['Risk Pattern Id']].values:
      if not value in riskPattern3NotIn4:
        riskPattern3NotIn4.append("'%s'"%value[0])

  riskPattern4NotIn3=list()
  for value in riskPattern4[['Risk Pattern Id']].values:
    if not value in riskPattern3[['Risk Pattern Id']].values:
      if not value in riskPattern4NotIn3:
        riskPattern4NotIn3.append("'%s'"%value[0])

  errors=""
  if len(riskPattern3NotIn4) != 0:
    errors+="The following risk patterns are in the ASVS v3 but not in the v4: %s.\n\n"%str(", ".join(riskPattern3NotIn4))
  if len(riskPattern4NotIn3) != 0:
    errors+="The following risk patterns are in the ASVS v4 but not in the v3: %s.\n\n"%str(", ".join(riskPattern4NotIn3))
  
  print(errors)

  return errors


def checkDuplicatedControlWithSameNameDifferentRef(path):
  #First we get the necessary control information.
  controls=list()
  for lib in os.listdir(str(path)):
    if lib.endswith(".xml"):
      root=sl.parse(str(path / lib), silence=True)
      for component in root.get_components().get_component():
        for control in component.get_controls().get_control():
          asvs3="No"
          asvs4="No"
          for standard in control.get_standards().get_standard():
            if standard.get_supportedStandardRef()[0:12] == "owasp-asvs4-":
              asvs4="Yes"
            if standard.get_supportedStandardRef()[0:11] == "OWASP-ASVS-":
              asvs3="Yes"            
          controls.append([
            root.get_ref(),
            component.get_ref(),
            control.get_ref(),
            control.get_name(),
            asvs3,
            asvs4
          ])
  
  # After that we create the DataFrames
  final=pd.DataFrame([], columns=['Library Id', 'Component Id', 'Control Id', 'Control Name', 'ASVS v3', 'ASVS v4'])
  dfm = pd.DataFrame(controls, columns=['Library Id', 'Component Id', 'Control Id', 'Control Name', 'ASVS v3', 'ASVS v4'])
  #dfm=dfm.drop_duplicates(['Control Id', 'Control Name'])
  controlNames=dfm['Control Name'].drop_duplicates()
  for name in controlNames:
    data=dfm[dfm['Control Name'] == name].drop_duplicates(['Control Id', 'Control Name'])
    # We check if the countermeasures don't belong to ASVS v3 and ASVS v4
    dataWithErrors=data[(data['ASVS v3'] == "No") & (data['ASVS v4'] == "No")].sort_values(by=['Control Name']).drop_duplicates(['Control Id', 'Control Name', 'ASVS v3', 'ASVS v4'])
    # We check if the countermeasures belong to ASVS v3 and ASVS v4
    dataASVS4=data[(data['ASVS v3'] == "Yes") & (data['ASVS v4'] == "Yes")].sort_values(by=['Control Name']).drop_duplicates(['Control Id', 'Control Name', 'ASVS v3', 'ASVS v4'])
    #We check if there are controls with same name but different id
    if len(dataASVS4) > 1:
      final=final.append(dataASVS4)
  # If there is any error, we show it in a HTML file.
  if len(final) > 0:
    with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
      path_output=Path.cwd() / "outputFiles" / "test_duplicate_control_name_different_ref.html"
      final.to_html(str(path_output))
      print("Review the errors in the following HTML file: '%s'"%path_output)

    return False
  else:
    return True

def checkCopyrightInAllLibrarires(path):
  errors=""
  text1="<!--Copyright (c) 2012-%s Continuum Security.  All rights reserved.The content of this library is the property of Continuum Security SL and may only be used in whole or in part with a valid license for IriusRisk.-->"%date.today().year
  for lib in os.listdir(path):
    if lib.endswith(".xml"):
      found=False
      with open(str(path / lib), 'r') as f:
        for line in f.readlines():
          if line.find(text1) != -1:
            found=True
        if not found:
          errors+="The library %s has not got the Copyright in the xml file.\n"%lib.replace(".xml","")
        f.close()
  return errors


def checkIntegrityOfCategoryComponentsFromLibrary(path_library):
  errors=list()
  root=sl.parse(str(path_library), silence=True)
  categoryComponents = root.get_categoryComponents()
  for categoryComponent in categoryComponents.get_categoryComponent():
    if categoryComponent.get_ref() == "":
      errors.append("Empty Id for the Category Component with the name '%s'." %categoryComponent.get_name())
    if categoryComponent.get_name() == "":
      errors.append("Empty Name for the Category Component with the ref '%s'." %categoryComponent.get_ref())

  return errors

# with this method, we obtain the references, standards and implementation and we convert it to DataFrame
def getControlData(path_library):
  data=list()
  root=sl.parse(str(path_library), silence=True)
  for component in root.get_components().get_component():
    for control in component.get_controls().get_control():
      for standard in control.get_standards().get_standard():
        data.append([root.get_ref(), component.get_ref(), control.get_ref(), standard.get_supportedStandardRef(), standard.get_ref(), "", "", "", ""])
      for reference in control.get_references().get_reference():
        data.append([root.get_ref(), component.get_ref(), control.get_ref(), "", "", reference.get_name(), reference.get_url(), "", ""])
      for implementation in control.get_implementations().get_implementation():
        data.append([root.get_ref(), component.get_ref(), control.get_ref(), "", "", "", "", implementation.get_platform().strip(), implementation.get_desc().strip()])
  
  data = pd.DataFrame(data, columns=['Library Id', 'Component Id', 'Control Id', 'Supported Standard Ref', 'Standard Ref', 'Reference Name', 'Reference URL', 'Implementation Platform', 'Implementation Desc'])

  return data

# We compare two DataFrames (with and without duplicates rows) and we return an error if there is any duplicated row
def checkDuplicatedByDataFrames(data, dataNoDupls, textType):
  errors=""
  if len(data) != len(dataNoDupls):
    equals=data.eq(dataNoDupls)
    result=data[data.index.isin(equals[equals['Library Id'] == False].index.values)]   
    for index, row in result.iterrows():
      errors+="There are duplicated %s in the countermeasure '%s' from the component '%s'.\n"%(textType, row['Control Id'], row['Component Id'])
  return errors

# We get the data from the countermeasures, order them, compared the dataframes (with and without duplicated rows) and return the errors.
def checkDuplicatedItemsPerControl(path_library, sort_values, textType):  
  data = getControlData(path_library)  
  data=data[sort_values]
  data=data[data[sort_values[2]]!=""]  
  data=data[data[sort_values[4]]!=""]  
  data = data.sort_values(by=sort_values)
  dataWithoutDuplicated=data.drop_duplicates()  

  return checkDuplicatedByDataFrames(data, dataWithoutDuplicated, textType)
  
def searchSpanTag(root, error, controlRef):
  msg=""
  error=False
  for i in root:    
    if i.tag == "span":
      error=True
      if searchSpanTag(i, error, controlRef):
        msg="Tag span found in the control id '%s' and tag '%s'.\n"%(controlRef, i.tag)
    
  return error, msg

def checkTagsFromString(data, Ref, LibraryFileName, errors):
  #Allowed tags from Jsoup Filter in IriusRisk
  WHITELIST_TAGS = ["a", "b", "blockquote", "br", "caption", "cite", "code", "col", "colgroup", "dd", "div", "dl", "dt", "em", "h1", "h2", "h3", "h4", "h5", "h6",
  "i", "img", "li", "ol", "p", "pre", "q", "small", "span", "strike", "strong","sub", "sup", "table", "tbody", "td", "tfoot", "th", "thead", "tr", "u", "ul", "font"]
  decodedData = html.unescape(data)

  soup = BeautifulSoup(decodedData, 'html.parser')
  # error+="Invalid HTML tag: '%s' for the Ref: %s from the Library: %s.\n"%(tag.name, Ref, LibraryFileName)
  for tag in soup.findAll(True):
      #print("Detected TAG Name: " + tag.name)
      if tag.name not in WHITELIST_TAGS:
        errors.append([LibraryFileName, Ref, tag.name])
      
  return errors

def checkTagsOfControlsOrWeaknesses(array, tag, exceptions):
  errors=list()
  for index, it in array.iterrows():
    if not it['Id'] in exceptions:
      errors=checkTagsFromString(it[tag], it['Id'], it['Library filename'], errors)
  
  dfm = pd.DataFrame(errors, columns=['Library File Name', 'Control Id', 'Tag name'])
  dfm=dfm.sort_values(by=['Library File Name', 'Control Id'])
  dfm=dfm.groupby(['Library File Name', 'Control Id'])['Tag name'].apply(lambda x: "{%s}" % ', '.join(x))
  err=""
  for index, row in dfm.iteritems():
    err+="Invalid HTML tags in countermeasure '%s' from the Library '%s': %s.\n"%(index[1], index[0], row.replace("{","").replace("}",""))
  return err

def splitAndCheckAscii(data, Ref, LibraryFileName):
    isAscii = True
    datas = data.split()
    for t in datas:
        if not t.isascii():
            print("Library: "+LibraryFileName+" Reference: "+Ref+" ->The following string is not ASCII: " + t)
            isAscii = False

    return isAscii

def unescapeHTML(data):
    decodedData = html.unescape(data)

    return decodedData

def extractTextFromHtml(data):
    soup = BeautifulSoup(data, 'html.parser')
    text = soup.find_all(text=True)

    output = ''
    blacklist = [
        'style'
    ]

    for t in text:
        if t.parent.name not in blacklist:
            output += '{} '.format(t)

    return output

def checkAsciiFromString(data, Ref, LibraryFileName, errors):
  
  decodedData = unescapeHTML(data)
  text = extractTextFromHtml(decodedData)

  if not splitAndCheckAscii(text, Ref, LibraryFileName):
    errors.append([LibraryFileName, Ref])
      
  return errors

def checkAsciiOfControlsOrWeaknesses(array, tag, exceptions):
  errors=list()
  for index, it in array.iterrows():
    if not it['Id'] in exceptions:
      errors=checkAsciiFromString(it[tag], it['Id'], it['Library filename'], errors)
  
  dfm = pd.DataFrame(errors, columns=['Library File Name', 'Control Id'])
  dfm=dfm.sort_values(by=['Library File Name', 'Control Id'])
  dfm=dfm.groupby(['Library File Name', 'Control Id']).apply(lambda x: "{%s}" % ', '.join(x))
  err=""
  for index, row in dfm.iteritems():
    err+="Non ASCII content in reference '%s' from the Library '%s'.\n"%(index[1], index[0])
  return err


def checkDuplicatedControlsPerComponentFromLibrary(path_library):
  errors=""
  
  root=sl.parse(str(path_library), silence=True)
  for component in root.get_components().get_component():
    controls=list()
    for control in component.get_controls().get_control():
      controls.append(control.get_ref())
  
    controls.sort()
    before=""
    for i in controls:
      if i == before:
        errors+="Component: %s --> Countermeasure: %s\n "%(component.get_ref(), i)
      before=i
  if errors != "":
    errors="Some duplicates controls with the same ref was found: %s.\n"%errors
  return errors


def checkDuplicatedControlsInThreat(path_library):
  errors = []

  root = etree.parse(str(path_library))

  for component in root.iter('component'):
    threats = list(component.iter('threat'))
    for threat in component.iter('threat'):
      controlRefs = [control.attrib['ref'] for control in list(threat.find("controls").iter("control"))]
      wControlRefs = [wControl.attrib['ref'] for wControl in list(threat.find("weaknesses").iter("control"))]
      duplicated = []
      for c in controlRefs:
        if wControlRefs.count(c) > 1:
          duplicated.append(c)
      if duplicated != []:
        errors += f"Component: {component.attrib['ref']} Threat: {threat.attrib['ref']} --> has duplicated control/s {str(duplicated)}\n "

  if errors == []:
    return True, ""
  else:
    return False, "Duplicated controls: " + str(errors)

def checkDuplicatedWeaknessesPerComponentFromLibrary(path_library):
  errors=""
  
  root=sl.parse(str(path_library), silence=True)
  for component in root.get_components().get_component():
    weaks=list()
    for weak in component.get_weaknesses().get_weakness():
      weaks.append(weak.get_ref())
  
    weaks.sort()
    before=""
    for i in weaks:
      if i == before:
        errors+="Component: %s --> Weakness: %s\n "%(component.get_ref(), i)
      before=i
  if errors != "":
    errors="Some duplicates weakness with the same ref was found: %s.\n"%errors
  return errors

def checkDuplicatedThreatsPerUseCaseAndComponentFromLibrary(path_library):
  errors=""
  
  root=sl.parse(str(path_library), silence=True)
  for component in root.get_components().get_component():
    
    for usecase in component.get_usecases().get_usecase():
      threats=list()
      for threat in usecase.get_threats().get_threat():
        threats.append(threat.get_ref())
    
      threats.sort()
      before=""
      for i in threats:
        if i == before:
          errors+="Component: %s --> Threat: %s\n "%(component.get_ref(), i)
        before=i
  if errors != "":
    errors="Some duplicates threats with the same ref was found: %s.\n"%errors
  return errors


def checkDuplicatedComponentsFromLibrary(path_library):
  errors=""
  components=list()
  root=sl.parse(str(path_library), silence=True)
  for component in root.get_components().get_component():
    components.append(component.get_ref())
  
  components.sort()
  lastComponent=""
  for component in components:
    if component == lastComponent:
      errors+="%s, "%component
    lastComponent=component
  if errors != "":
    errors="Some duplicates components with the same ref was found: %s."%errors[0:-2]
  return errors

def checkIntegrityOfComponentDefinitionsFromLibrary(path_library):
  errors=list()
  componentRefs=list()
  root=sl.parse(str(path_library), silence=True)
  componentDefinitions = root.get_componentDefinitions()
  for component in root.get_components().get_component():
    componentRefs.append(component.get_ref())
  for componentDefinition in componentDefinitions.get_componentDefinition():
    if componentDefinition.get_ref() == "":
      errors.append('Empty Id for the Component Definition with the name %s.' %componentDefinition.get_name())
    if componentDefinition.get_name() == "":
      errors.append('Empty Name for the Component Definition with the ref %s.' %componentDefinition.get_ref())
    if componentDefinition.get_categoryRef() == "":
      errors.append('Empty CategoryRef for the Component Definition with the ref %s.' %componentDefinition.get_ref())
    for riskPattern in componentDefinition.get_riskPatterns().get_riskPattern():
      if not riskPattern.get_ref() in componentRefs:
        errors.append("Risk Pattern '%s' for the Component Definition with the ref '%s' wasn't found."%(riskPattern.get_ref(), componentDefinition.get_ref()))
  return errors

def checkIfAllCountermeasuresAreWithRecommendedStatus(path_library):
  errors=list()
  root=sl.parse(str(path_library), silence=True)
  for component in root.get_components().get_component():
    for control in component.get_controls().get_control():
      if control.get_state() != "Recommended":
        errors.append("Countermeasure with ref '%s' hasn't got the state as Recommended."%control.get_ref())
  
  return errors

def checkIfExistsUnassignedCountermeasures(path_library):
  errors=list()
  root=sl.parse(str(path_library), silence=True)
  for component in root.get_components().get_component():
    controlsRef1=list()
    controlsRef2=list()
    controlsComponentTypeRef = [c.get_ref() for c in component.get_controls().get_control()]
    for useCase in component.get_usecases().get_usecase():
      for threat in useCase.get_threats().get_threat():
        controlsThreatTypeRef = [c.get_ref() for c in threat.get_controls().get_control()]
        for weakness in threat.get_weaknesses().get_weakness():
          for control in weakness.get_controls().get_control():
            #First we check that the control ref appears in the location component/controls/control
            if (not control.get_ref() in controlsComponentTypeRef) and (not control.get_ref() in controlsRef1):
              controlsRef1.append(control.get_ref())
              errors.append("Component: '%s': Countermeasure with ref '%s' not found in the control list for the component" % 
                (component.get_ref(), control.get_ref()))
            #Secondly we check that the control ref also appears in the location component/usecases/usecase/threats/threat/controls/control
            if (not control.get_ref() in controlsThreatTypeRef) and (not control.get_ref() in controlsRef2):
              controlsRef2.append(control.get_ref())
              errors.append("Component: '%s': Countermeasure with ref '%s' not found in the control list for the threat '%s'" % 
                (component.get_ref(), control.get_ref()), threat.get_ref())

  return errors

def checkIfExistsUnassignedWeaknesses(path_library):
  errors=list()
  root=sl.parse(str(path_library), silence=True)
  for component in root.get_components().get_component():
    weaknessesThreatTypeRef=list()
    weaknessesComponentTypeRef = [w.get_ref() for w in component.get_weaknesses().get_weakness()]
    for useCase in component.get_usecases().get_usecase():
      for threat in useCase.get_threats().get_threat():
        for weakness in threat.get_weaknesses().get_weakness():
          if (not weakness.get_ref() in weaknessesComponentTypeRef) and (not weakness.get_ref() in weaknessesThreatTypeRef):
            weaknessesThreatTypeRef.append(weakness.get_ref())
            errors.append("Component: '%s': The weakness with ref '%s' is not assigned to any threat" % (component.get_ref(), weakness.get_ref()))
    
  return errors

def checkIfStandardReferenceIsEmpty(path_library):
  errors=list()
  root=sl.parse(str(path_library), silence=True)
  for component in root.get_components().get_component():
    for control in component.get_controls().get_control():
      for standard in control.get_standards().get_standard():
        if standard.get_supportedStandardRef() == "":
          errors.append("Integrity: the Supported standard Ref in the countermeasure '%s' is empty."%control.get_ref())
        if standard.get_ref() == "":
          errors.append("Integrity: the Reference in the countermeasure '%s' is empty."%control.get_ref())

  return errors

def checkIfAsvs4ControlsHaveAsvs3Standards(path_library):
  errors=list()
  #Static list of new ASVSv4 native controls
  asvs4ControlRefs = [
  'apply-patches-to-server', 'APP-SANDBOX', 'configuration-integrity', 'crypto-operations', 'CWE-306-AUTH',
  'CWE-306-STR', 'CWE-367-TOCTOU', 'CWE-494-BINSIG', 'CWE-524',
  'CWE-646-CSP', 'CWE-923-SEGREG', 'deny-default-enf', 'dyn-exec', 'error-handling-centralised',
  'EU-GDPR-BACKUP', 'EU-GDPR-CONSENT-MECHANISM', 'excessive-permissions', 'FEAT-ACC-CTRL', 'follow-jwt-standard-generation-token',
  'graphql-authorization-logic', 'graphql-whitelisting', 'harden-http-headers', 'http-headers-authentication', 'identify-dns-domains',
  'INS-CLIENT', 'LEAST-PRIV-ENF', 'lib-management', 'look-up-secret-auth', 'memory-safe-ops',
  'network-rate-limit-login', 'not-store-sensitive-data-client-side', 'password-reset-email-best-practices', 'pseudo-random-number-generator', 'remove-function-collect-privacy-data-without-consent', 'require-use-strong-passwords', 'require-use-strong-passwords-with-ui', 'rest-content-type-val', 'revoke-compromised-authentication-tokens', 'same-encoding-parsers', 'scan-antivirus', 'SEC-DEPLOY', 'SEC-FEATURES', 'secure-attributes-of-cookies',
  'secure-communication-ra-and-csp', 'secure-file-storage', 'secure-password-recovery', 'secure-recovery-token-reset-account', 'secure-session-generation-and-expiration',
  'SER-UNTRUST', 'sign-ws-security', 'store-passwords-unrecoverable-form', 'template-val', 'TIME-STATE',
  'use-analysis-static-code'
  ]
  
  root=sl.parse(str(path_library), silence=True)
  for component in root.get_components().get_component():
    for control in component.get_controls().get_control():
      if control.get_ref() in asvs4ControlRefs:
        for standard in control.get_standards().get_standard():
          #We check if the new ASVSv4 control has any ASVSv3 standard
          if standard.get_supportedStandardRef().find("OWASP-ASVS-") >= 0:
            errors.append(control.get_ref())

  uniqueErrors = list(dict.fromkeys(errors))
  return uniqueErrors

def getWeaknessesFromAllLibraries(path_libraries):
  weaknessList=list()
  for library in os.listdir(str(path_libraries)):
    if library.endswith(".xml"):
        root= sl.parse(str(path_libraries / library), silence=True)
        for component in root.get_components().get_component():
          for weakness in component.get_weaknesses().get_weakness():
            weaknessList.append([
              str(library),
              weakness.get_ref(),
              weakness.get_name(),
              weakness.get_desc(),
              weakness.get_state(),
              weakness.get_impact(),
              weakness.get_issueId(),
              weakness.get_test().get_expiryDate(),
              weakness.get_test().get_expiryPeriod(),
              weakness.get_test().get_steps(),
              weakness.get_test().get_notes(),
              str([[r.get_name(), r.get_url()] for r in weakness.get_test().get_references().get_reference()]),
              weakness.get_test().get_source().get_result(),
              str(weakness.get_test().get_udts().get_udt())
            ]
            )
  columns=['Library filename', 'Id', 'Name', 'Description', 'State', 'Impact', 'Issue Id', 'Test Expiry Date', 'Test Expiry Period', 'Test Steps', 'Test Notes', 'Test References', 'Test Source Result', 'udts']
  dfm=pd.DataFrame(weaknessList, columns = columns)
  dfm=dfm.sort_values(by=['Id', 'Name'])
  return dfm, columns


def getControlsFromAllLibraries(path_libraries):
  controlList=list()
  for library in os.listdir(str(path_libraries)):
    if library.endswith(".xml"):
        root= sl.parse(str(path_libraries / library), silence=True)
        for component in root.get_components().get_component():
          for control in component.get_controls().get_control():
            standards=["%s - %s"%(s.get_supportedStandardRef(), s.get_ref()) for s in control.get_standards().get_standard()]
            standards.sort()
            standards=",\n".join(standards)

            controlList.append([
              str(library),
              control.get_ref(),
              control.get_name(),
              control.get_desc(),
              control.get_issueId(),
              control.get_platform(),
              control.get_cost(),
              control.get_risk(),
              control.get_state(),
              control.get_owner(),
              control.get_library(),
              control.get_source(),
              ",\n".join(["%s - %s"%(i.get_platform(),i.get_desc()) for i in control.get_implementations().get_implementation()]),
              ",\n".join(["%s - %s"%(r.get_name(),r.get_url()) for r in control.get_references().get_reference()]),
              standards,
              str(control.get_udts().get_udt()),
              control.get_test().get_expiryDate(),
              control.get_test().get_expiryPeriod(),
              control.get_test().get_steps(),
              control.get_test().get_notes(),
              ",\n".join(["%s -%s"%(r.get_name(), r.get_url()) for r in control.get_test().get_references().get_reference()]),
              control.get_test().get_source().get_result()
              ])
  columns=['Library filename', 'Id', 'Name', 'Description', 'Issue Id', 'Platform', 'Cost', 'Risk', 'State', 'Owner', 'Library', 'Source', 'Implementations', 'References', 'Standards',  'Udts', 'Test Expiry Date', 'Test Expiry Period', 'Test Steps', 'Test Notes', 'Test References', 'Test Source Result']
  dfm=pd.DataFrame(controlList, columns = columns)
  dfm=dfm.sort_values(by=['Id', 'Name'])
  return dfm, columns

def extractResultsFromDataFrame(dataFrame, itemType, columns):
  errorsFrame=pd.DataFrame()
  errors=""
  columns=columns[1:]
  dataFrame=dataFrame.drop_duplicates(columns)
  shownItems=list()
  total=['Id', 'Name', 'Library filename']
  for index, row in dataFrame.iterrows():
    if not row['Id'] in shownItems:
      duplicated = dataFrame.loc[lambda df: df['Id'] == row['Id']]
      duplicated = duplicated.loc[lambda df: df['Name'] == row['Name']]
      if len(duplicated) > 2:
        whereDupls=list()
        errorsFrame=pd.concat([errorsFrame, duplicated])
        for i in duplicated.columns:
          if i != 'Id' or i != 'Name':
            noDupls=duplicated[i].drop_duplicates()
          if len(noDupls) > 1:
            whereDupls.append(i)
            if not i in total:
              total.append(i)
        errors+="The %s with id '%s' has got diferences in: %s.\n"%(itemType, row['Id'], str(whereDupls).replace("[","").replace("]",""))        
        shownItems.append(row['Id'])
  
  if errors != "":
    output_path=Path.cwd() / "tests" / "outFiles" / str("output_sameIdDifferentData_"+itemType+".html")
    errors+="\nThere is more information about the differences in the following path: %s.\n"%output_path
    pd.set_option('display.max_colwidth', -1)
    errorsFrame=errorsFrame.dropna(axis=0, how='all')
    for i in total:
      if i != 'Cost':
        errorsFrame[i]=errorsFrame[i].str.replace(",\n",",<br/>")
        errorsFrame[i]=errorsFrame[i].str.replace("\n","")
    errorsFrame[total].to_html(str(output_path), escape=False,justify='center', notebook=True, sparsify=False)
  return errors

def extractCountermeasuresWithDifferentStandards(df):
  errors=""
  #First we filter rows with the same Id and Name
  df2 = df[df.duplicated(subset=['Id', 'Name'], keep=False)].sort_values(['Id', 'Standards'])

  #We create a new column to store if one raw value for column Standards is not the same as the following. If yes we get a True -> 1 as integer
  df2['changed_standards'] = df2['Standards'].ne(df2['Standards'].shift().bfill()).astype(int)
  #We create a new column to store if one raw value for column Name is not the same as the following. If yes we get a True -> 1 as integer
  df2['changed_Id'] = df2['Id'].ne(df2['Id'].shift().bfill()).astype(int)

  #We are looking for events in which name is not changed but standards yes
  df3 = df2[(df2['changed_standards'] == 1) & (df2['changed_Id'] == 0)]

  if (len(df3) > 0):
    pd.set_option('display.max_colwidth', -1)
    pd.set_option('max_columns', None)
    output_path=Path.cwd() / "tests" / "outFiles" / str("output_sameIdDifferentStandards.html")
    df2[['Id','Name', 'Library filename', 'Standards', 'changed_standards', 'changed_Id']].to_html(str(output_path), escape=False,justify='center', notebook=True, sparsify=False)
    print("You can find a detailed HTML report of the failed integrity test for Standards in the following path:\n" + str(output_path))
    errors = "Number of failed controls for Standards Integrity test: " + str(len(df3)) + "\n"
    for index, row in df3.iterrows():
      #We calculate the number of repeated controls
      df4 = df2[df2['Id'] == row["Id"]]
      errors += "\n* Integrity test for Standards failed for #Library: " + str(row["Library filename"])
      errors += " #Control ->Id: " + str(row["Id"]) + " ->Name: " + str(row["Name"]) + " ->Repetitions: " + str(len(df4))
      #We print the first value of Standards for the Control Id
      baselineStandards = df4["Standards"].iloc[0]
      currentStandards = row["Standards"]
      errors += "\nMissed Standards:\n"
      errors += " #".join(standardsDiff(baselineStandards, currentStandards))
      #We print the current value of Standards for the Control Id
      errors += "\nAdded Standards:\n"
      errors += " #".join(standardsDiff(currentStandards, baselineStandards))
  
  return errors

def standardsDiff(first, second):
  first_list = first.replace("\n", "").split(",")
  second_list = second.replace("\n", "").split(",")
  second_list = set(second_list)
  return [item for item in first_list if item not in second_list]

def getStandardsFromCountermeasures(path_libraries):
  control_standard=list()
  for library in os.listdir(str(path_libraries)):
    if library.endswith(".xml"):
        root= sl.parse(str(path_libraries / library), silence=True)
        for component in root.get_components().get_component():
          for control in component.get_controls().get_control():
            for standard in control.get_standards().get_standard():
              control_standard.append([standard.get_supportedStandardRef(), standard.get_ref()])
  
  dfm = pd.DataFrame(control_standard, columns=['Supported Standard Id', 'Standard Reference'])
  dfm.sort_values(by=['Supported Standard Id', 'Standard Reference'])
  dfm.drop_duplicates()
  return dfm

def checkEmptyWeaknesses(path_libraries, exceptions):
  errors = []
  for library in os.listdir(str(path_libraries)):
    if library.endswith(".xml"):
      root = etree.parse(str(path_libraries / library))
      for component in root.find("components").iter("component"):
        for threat in component.iter("threat"):
          for weakness in threat.iter("weakness"):
            controls = list(weakness.iter('control'))
            if not controls:
              if not component.attrib['ref'] in exceptions:
                errors.append(library + " Component -> " + component.attrib['ref'] + " Weakness -> " + weakness.attrib['ref'])

  if not errors:
    return ""
  else:
    return "Weaknesses without controls: "+str(errors)

def checkOrphanedControls(path_libraries):
  errors = []
  for library in os.listdir(str(path_libraries)):
    if library.endswith(".xml"):
      root = etree.parse(str(path_libraries / library))
      for threat in root.find("components").iter("threat"):
        controlRefs = [control.attrib['ref'] for control in list(threat.find("controls").iter("control"))]
        wControlRefs = [wControl.attrib['ref'] for wControl in list(threat.find("weaknesses").iter("control"))]
        for controlRef in controlRefs:
          if controlRef not in wControlRefs:
            errors.append(library + " -> " + controlRef)

  if not errors:
    return ""
  else:
    return "Orphaned controls: " + str(errors)

def checkCRLF(path_libraries):
  errors = []
  for library in os.listdir(str(path_libraries)):
    if library.endswith(".xml"):
      f = open(str(path_libraries / library))
      f.readline()

      # Check if the line separator is CRLF or CR
      if repr('\r\n') == repr(f.newlines): errors.append(library)
      if repr('\r') == repr(f.newlines):   errors.append(library)

  if not errors:
    return ""
  else:
    return "Libraries with CRLF or CR: " + str(errors)

def checkDuplicatedStandardsInControl(path_libraries):
  errors = []
  for library in os.listdir(str(path_libraries)):
    if library.endswith(".xml"):
      root = etree.parse(str(path_libraries / library))
      for component in root.find("components").iter("component"):
        for control in component.find("controls").iter("control"):
          l = [st.attrib["supportedStandardRef"] + "-" + st.attrib['ref'] for st in list(control.iter("standard"))]
          p = set([x for x in l if l.count(x) > 1])
          if len(p)!=0:
            errors.append(f"{library} -> {control.attrib['ref']} -> {str(p)}")

  if not errors:
    return ""
  else:
    return "Duplicated standards in controls: " + str(errors)

def checkWhitespacesInReferenceUrls(path_libraries):
  errors = []
  for library in os.listdir(str(path_libraries)):
    if library.endswith(".xml"):
      root = etree.parse(str(path_libraries / library))
      for component in root.find("components").iter("component"):
        for control in component.find("controls").iter("control"):
          references = list(control.iter("reference"))
          l = [reference.attrib['name'] for reference in references if " " in reference.attrib['url']]
          if len(l) != 0:
            errors.append(f"{library} -> {control.attrib['ref']} -> {str(l)}")

  if not errors:
    return ""
  else:
    return "URLs with whitespaces: " + str(errors)


def checkInconsistentControlNames(path_libraries):
  errors = []

  for library in os.listdir(str(path_libraries)):
    if library.endswith(".xml"):
      root = etree.parse(str(path_libraries / library))

      # ASVS4 flag off in Irius:
      #  - Controls that don´t have neither ASVSv4 nor ASVSv3.
      #  - Control that have ASVSv3 but not ASVSv4.
      #     Test: For these controls if control name collision -> Test failed
      # ASVS4 flag on in Irius:
      #  - Controls that don´t have neither ASVSv4 nor ASVSv3.
      #  - Control that have ASVSv4 but not ASVSv3.
      #     Test: For these controls if control name collision -> Test failed

      # Case 1: ASVS4 flag off

      failedASVS4OffDiffName = set()
      failedASVS4OffDiffRef = set()
      failedASVS4OnDiffName = set()
      failedASVS4OnDiffRef = set()

      controls = set()
      for component in root.iter('component'):
        for control in component.find('controls').iter('control'):

          standardList = list(control.iter('standard'))
          standardsRef = [x.attrib['supportedStandardRef'].lower() for x in standardList]
          asvs4list = [x for x in standardsRef if "owasp-asvs4" in x]

          # If none of its standards have asvs4 refs
          if len(asvs4list) == 0:
            controls.add(control)

      for control in controls:
        controlRef = control.attrib['ref']
        controlName = control.attrib['name']
        for c in controls:
          controlRef2 = c.attrib['ref']
          controlName2 = c.attrib['name']
          if controlRef2 == controlRef and controlName2 != controlName:
            if (controlRef, controlName, controlName2) not in failedASVS4OffDiffName \
              and (controlRef, controlName2, controlName) not in failedASVS4OffDiffName:
              failedASVS4OffDiffName.add((controlRef, controlName, controlName2))
          if controlName2 == controlName and controlRef2 != controlRef:
            if (controlName, controlRef, controlRef2) not in failedASVS4OffDiffRef \
              and (controlName, controlRef2, controlRef) not in failedASVS4OffDiffRef:
              failedASVS4OffDiffRef.add((controlName, controlRef, controlRef2))

      # Case 2: ASVS4 flag on

      controls = set()
      for component in root.iter('component'):
        for control in component.find('controls').iter('control'):

          standardList = list(control.iter('standard'))
          standardsRef = [x.attrib['supportedStandardRef'].lower() for x in standardList]
          asvs3list = [x for x in standardsRef if "owasp-asvs-" in x]

          if len(asvs3list) == 0:
            controls.add(control)

      for control in controls:
        controlRef = control.attrib['ref']
        controlName = control.attrib['name']
        for c in controls:
          controlRef2 = c.attrib['ref']
          controlName2 = c.attrib['name']
          if controlRef2 == controlRef and controlName2 != controlName:
            if (controlRef, controlName, controlName2) not in failedASVS4OnDiffName \
              and (controlRef, controlName2, controlName) not in failedASVS4OnDiffName:
              failedASVS4OnDiffName.add((controlRef, controlName, controlName2))
          if controlName2 == controlName and controlRef2 != controlRef:
            if (controlName, controlRef, controlRef2) not in failedASVS4OnDiffRef \
              and (controlName, controlRef2, controlRef) not in failedASVS4OnDiffRef:
              failedASVS4OnDiffRef.add((controlName, controlRef, controlRef2))


      # Finally we show the errors

      for x in failedASVS4OffDiffName:
        errors.append(f"ASVS4 OFF: Type1 -> {library} -> {x[0]} // Control Name 1: {x[1]} / Control Name 2: {x[2]}")

      for x in failedASVS4OffDiffRef:
        errors.append(f"ASVS4 OFF: Type2 -> {library} -> {x[0]} // Control Ref 1: {x[1]} / Control Ref 2: {x[2]}")

      for x in failedASVS4OnDiffName:
        errors.append(f"ASVS4 ON: Type1 -> {library} -> {x[0]} // Control Name 1: {x[1]} / Control Name 2: {x[2]}")

      for x in failedASVS4OnDiffRef:
        errors.append(f"ASVS4 ON: Type2 -> {library} -> {x[0]} // Control Ref 1: {x[1]} / Control Ref 2: {x[2]}")


  if not errors:
    return ""
  else:
    return "Non-consistent controls: " + str(errors)


def checkDuplicatedRiskPatternRefs(path_libraries):
  errors = []

  riskPatternFound = dict()
  for library in os.listdir(str(path_libraries)):
    if library.endswith(".xml"):
      root = etree.parse(str(path_libraries / library))
      for component in root.find("components").iter("component"):
        ref = component.attrib['ref']
        if ref not in riskPatternFound.keys():
          riskPatternFound[ref]=library
        else:
          errors.append(f"Risk pattern {ref} in {library} appears to be duplicated in {riskPatternFound[ref]}")

  if not errors:
    return ""
  else:
    return "Duplicated risk patterns: " + str(errors)


def checkInconsistentThreatAndWeaknessNames(path_libraries):
  errors = []

  for library in os.listdir(str(path_libraries)):
    if library.endswith(".xml"):
      root = etree.parse(str(path_libraries / library))

      alreadyFound = dict()
      for threat in root.iter('threat'):
        threatRef = threat.attrib['ref']
        threatName = threat.attrib['name']

        if threatRef not in alreadyFound:
          alreadyFound[threatRef]=threatName
        else:
          if threatName != alreadyFound[threatRef]:
            result = f"{library} -> Threat {threatRef} has different names"
            if result not in errors:
              errors.append(result)

      alreadyFound = dict()
      for component in root.iter('component'):
        for weakness in component.find('weaknesses').iter('weakness'):
          weaknessRef = weakness.attrib['ref']
          weaknessName = weakness.attrib['name']

          if weaknessRef not in alreadyFound:
            alreadyFound[weaknessRef] = weaknessName
          else:
            if weaknessName != alreadyFound[weaknessRef]:
              result = f"{library} -> Weakness {weaknessRef} has different names"
              if result not in errors:
                errors.append(result)

  if not errors:
    return ""
  else:
    return "Non-consistent names: " + str(errors)
