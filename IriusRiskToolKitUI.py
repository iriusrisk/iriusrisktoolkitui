import PySimpleGUI as sg   
from src.moduleJoinSeparate import joinFiles, separateFiles, removeAll 
from src.convertXmlToExcel import convertXmlToExcel
from src.convertExcelToXml import convertExcelToXml
from src.convertExcelToXml import convertRulesFromExcelToXML
from src.convertXmlToHtmlFile import generateHTML
from src.libraryDetails import readInfoFromXml
from src.mitigationValidator import libMitigationTest
from src.generateChangeLogFromVersions import generateChangeLog, getInfoFromChangeLog
from src.addStandardtoLibraries import addStandardToLibrary
from src.mergeLibraries import mergeLibrariesByPaths
from src.generateHtmlStandardvsCountermeasures import generateHtmlFromLibrariesAndStandard
from src.updateServerWithCloudComponents import *
from src.addReferencesFromExcel import addReferencesToLibrariesByExcelFile
from src.riskCalculator import calculateRiskToHTML
from pathlib import Path
import subprocess
from src.common import readConfig, writeConfig, testConnection
import os
import pandas as pd
import yaml

import logging
import webbrowser
import time


LOCATION =(0,0)
SIZE_ELEMENT=(100, 1)

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

#So that it does not complain about the Look and Feel in Windows
sg.change_look_and_feel('DefaultNoMoreNagging') 

#BUTTON_COLOR=('white', '#424632')
BUTTON_COLOR=('black', '#f2f2f2')
PATH_LIBS = Path.cwd() / "libraries"
PATH_TEMPLATES = Path.cwd() / "products"
PATH_EXCELS = Path.cwd() / "inputFiles" / "spreadSheetFiles" 

def selectionOfExcelFile(title, files, mainPath, home):
  home.Hide()
  mainRelativ=str(mainPath).replace(str(Path.cwd()), "..")
  libraries_path = Path.cwd() / "libraries"
  layout=[
    [sg.Text(title)],
    [sg.Text("Select the Excel file (Working directory: '%s'):"%mainRelativ), sg.InputCombo(files)],
    [sg.Text("Do you want to replace the libraries in the directory '%s'?"%libraries_path), sg.Checkbox(text='')],
    [sg.Submit(), sg.Cancel()]
  ]      
  win = sg.Window(title, layout, location=LOCATION)  
  win.UnHide()
  while True:
    ev, values = win.Read() 
    if ev is "Cancel" or ev == 'Exit':  
      win.Close()  
      home.UnHide()
      return "", ""
    if ev is "Submit":
      win.Close()  
      home.UnHide()  
      return values[0], values[1]

def selectionOfExcelRulesFile(title, files, mainPath, home):
  home.Hide()
  mainRelativ=str(mainPath).replace(str(Path.cwd()), "..")
  libraries_path = Path.cwd() / "outFiles" / "rulesEditorLibraries"
  layout=[
    [sg.Text(title)],
    [sg.Text("Select the Excel file (Working directory: '%s'):"%mainRelativ), sg.InputCombo(files)],
    [sg.Submit(), sg.Cancel()]
  ]      
  win = sg.Window(title, layout, location=LOCATION)  
  win.UnHide()
  while True:
    ev, values = win.Read() 
    if ev is "Cancel" or ev == 'Exit':
      win.Close()  
      home.UnHide()
      return ""
    if ev is "Submit":
      win.Close()  
      home.UnHide()  
      return values[0]

def startProgressBar(home):
  home.FindElement('progbar').Update("Ready!", text_color='white', background_color='royal blue')

def progressBar(home):
  home.FindElement('progbar').Update("Loading ...", text_color='white', background_color='DarkOrange3')

def finishProgressBar(home):
  home.FindElement('progbar').Update("Done", text_color='white', background_color='green')

class Data:
  def __init__(self):
    self.files = []
    self.apitoken = ""
    self.serverUrl = ""
    self.selectedStandard_path = ""
    self.parts=""
    libraryMaster = "" 
    libraryNewVersion = ""
    self.normalChangeLog=""


def getChangeLogLayout():
  files = [
    [sg.Text("You can generate the Change Log for all libraries from the following paths (by default, you shall not select any file):")],
    [sg.Text(" - Last release ('/inputFiles/lastRelease) "), sg.Button("Folder Last Release", key='showFolderLastRelease', button_color=BUTTON_COLOR)],
    [sg.Text(" - Current release ('/inputFiles/currentRelease) "), sg.Button("Folder Current Release", key='showFolderCurrentRelease', button_color=BUTTON_COLOR)],
    [sg.Text("Or generate the Change Log from two files (if the following File Browse are filled:")],
    [sg.Text('Select the old library:'), sg.Input(key='fileOldLibraryInput'), sg.FileBrowse(key='fileOldLibrary', button_color=BUTTON_COLOR)],
    [sg.Text('Select the new library:'), sg.Input(key='fileNewLibraryInput'), sg.FileBrowse(key='fileNewLibrary', button_color=BUTTON_COLOR)]
  ]
  return files

def getLayoutExcels():
  files=list()
  for excel in os.listdir(str(PATH_EXCELS)):
    files.append([sg.Checkbox(excel, key=excel, default=False)])

  files.append([sg.Button("Select all files", key='selectAllFiles', button_color=BUTTON_COLOR)])
  files.append([sg.Text('Filename:'), sg.Input(key='fileBrowseValueExcel'), sg.FileBrowse(key='browseExcel')])
  
  layout=[
    [sg.Frame("Select the Excel file to convert in XML (working directory: '../inputFiles/spreadSheetFiles/'):", files, key='excels')]
  ]
  return layout

def getLayoutUpgrade():
  path=Path.cwd() / "inputFiles" / "libsToMerge"
  mainRelativ=str(PATH_LIBS).replace(str(Path.cwd()), "..")
  secRelativ=str(path).replace(str(Path.cwd()), "..")
  arrayMaster=list()
  for lib in os.listdir(str(PATH_LIBS)):
    if lib.endswith(".xml"):
      arrayMaster.append(lib.replace(".xml", ""))

  arrayNewLibraries=list()
  for lib in os.listdir(str(path)):
    if lib.endswith(".xml"):
      arrayNewLibraries.append(lib.replace(".xml", ""))

  layout=[
    [sg.Text("Select the main library (Working directory: '%s'):"%mainRelativ), sg.InputCombo(arrayMaster, key='libraryMaster')],
    [sg.Text("Select the second library (Working directory: '%s'):"%secRelativ), sg.InputCombo(arrayNewLibraries, key='libraryNewVersion')]
  ]
  return layout

def getLayoutLibs():
  libs=list()
  for lib in os.listdir(str(PATH_LIBS)):
    if lib.endswith(".xml"):
      libs.append([sg.Checkbox(lib.replace(".xml", ""), key=lib.replace(".xml", ""), default=False)])

  libs.append([sg.Button("Select all libraries", key='selectAllLibs', button_color=BUTTON_COLOR)])
  libs.append([sg.Text('Filename:'), sg.Input(key='fileBrowseValue'), sg.FileBrowse(key='browse')])
  standardList=os.listdir(str(Path.cwd() / "inputFiles" / "standardsFiles"))
  standards=[[sg.Text("Select the option:", key='textStandards'), sg.InputCombo(standardList, key='comboStandards')]]
  options=[[sg.Text("Select the option:", key='textOptions'), sg.InputCombo(['Risk patterns & Rules', 'Risk patterns', 'Rules'], key='comboOptions')]]

  existingStandardList=list()
  path_info_standards=Path.cwd() / "inputFiles" / "descriptionOfStandards"
  for i in os.listdir(str(path_info_standards)):
    existingStandardList.append(i.replace("standard_","").replace("_info.csv",""))
  existingStandards = [[sg.Text("Select the standard:", key='textExistingStandards'), sg.InputCombo(existingStandardList, key='comboExistingStandards')]]

  serverUrl, apiToken, errorMessage = readConfig()
  serverConfig=[
    [sg.Text("Sever configurations:")],
    [sg.Text("Server url:"), sg.InputText(serverUrl, key='urlServer')],
    [sg.Text("Api Token:"), sg.InputText(apiToken, key='apiToken')],
    [sg.Button("Test Connection", key='test-connection')],
    [sg.Text("Error message:"), sg.InputText(errorMessage, key='errorMessage')]
  ]  

  
  layout=[
    [sg.Frame("Select the library or libraries to use (working directory: '../libraries/'):", libs, key='libs'),
    sg.Frame("Options:", options, key='options'),
    sg.Frame("Standards:", standards, key='standards'),
    sg.Frame("Server Configuration:", serverConfig, key='serverConfig'),
    sg.Frame("Server Configuration:", existingStandards, key='existingStandards')]
  ]

  return layout


def getLayoutProducts():
  products = list()
  for product in os.listdir(str(PATH_TEMPLATES)):
    if product.endswith(".xml"):
      products.append([sg.Checkbox(product.replace(".xml", ""), key=product.replace(".xml", ""), default=False)])

  products.append([sg.Button("Select all products", key='selectAllProducts', button_color=BUTTON_COLOR)])
  products.append([sg.Text('Filename:'), sg.Input(key='fileBrowseValueProduct'), sg.FileBrowse(key='browseProduct')])

  layout = [
    [sg.Frame("Select the product or products to use (working directory: '../products/'):", products, key='products')]
  ]

  return layout

def checkConnection(ev, home, values):
  if ev == "test-connection":
    msg=testConnection(values['urlServer'], values['apiToken'])
    home.FindElement(key="errorMessage").Update(msg)

def showLinks(links, results, home):
  if len(links) > 0 or results != "":
    home.Hide()
    layout=list()
    for link in links:
      if str(link).endswith(".html") or str(link).endswith(".xlsx") or str(link).endswith(".xls"):          
        layout.append([
          sg.Text(link.name, size=(30,1)), 
          sg.Button('Open', key='open'+str(link), button_color=BUTTON_COLOR, size=(5, 1))
          ])
      
    lay = [[sg.Frame("Results", [[sg.Multiline(results, size=(100, 25))]])],
    [sg.Frame("Links to be opened", layout)],
    [sg.Button("Ok")]
    ]
    win = sg.Window("Details", location=LOCATION)
    win.Layout(lay)
    while True:
      ev, values = win.Read()
      if ev is "Ok" or ev == 'exit':         
        win.Close()  
        home.UnHide()
        return "" 

      else:
        if ev.startswith("open"):
          ev=Path(ev[4:])
          if ev in links:
            if ev.suffix == ".html":
              webbrowser.open('file://' + str(links[links.index(ev)]))
            if ev.suffix == ".xlsx" or ev.suffix == ".xls":
              try:
                subprocess.Popen("start \"excel.exe\" '%s'"%str(ev))
              except:
                try:
                  subprocess.Popen('libreoffice \"'+str(ev)+'\"', shell=True)
                except:
                  try:
                    subprocess.Popen("libreoffice.exe", str(ev), shell=True)
                  except:
                    sg.Popup("We cannot find the program to open the Excel File.")
              
          

def showDetailsChangeLog(currentData, oldData, home):
  tabs=currentData['Library Name'].drop_duplicates().values.tolist()
  header_list = currentData.columns.values.tolist()
  group=list()
  for tab in tabs:
    tabData1=currentData[currentData['Library Name'] == tab]
    tabData1=tabData1.drop('Library Name', axis=1)
    tabData1=tabData1.values.tolist()

    tabData2=oldData[oldData['Library Name'] == tab]
    tabData2=tabData2.drop('Library Name', axis=1)
    tabData2=tabData2.values.tolist()
    if tabData2 == []:
      tabLayout=[[
      sg.Table(values=tabData1,  headings=header_list[1:], display_row_numbers=False, justification='left', auto_size_columns=True, background_color='white', alternating_row_color='lightgrey', num_rows=min(25,len(currentData)))]
      ]
    else:
      tabLayout=[
        [sg.Text("Current Version", size=(96,1), justification='left'), sg.Text("Last Version", size=(100,1), justification='left')],
        [
        sg.Table(values=tabData1,  headings=header_list[1:], display_row_numbers=False, justification='left', auto_size_columns=True, background_color='white', alternating_row_color='lightgrey', num_rows=min(25,len(currentData))),
        sg.Table(values=tabData2,  headings=header_list[1:], display_row_numbers=False, justification='left', auto_size_columns=True, background_color='white', alternating_row_color='lightgrey', num_rows=min(25,len(currentData)))
        ]
        ] 
    group.append([sg.Tab(tab, tabLayout)])
  
  layout=[[sg.TabGroup(group)], [sg.Button("OK")]]
  win = sg.Window("Details", location=LOCATION)
  win.Layout(layout)
  while True:
    ev, values = win.Read()
    if ev is "OK" or ev == 'exit':  
      win.Close()  
      home.UnHide()
      return "" 


def showDetails(totalData, home):
  tabs=totalData['Library Name'].drop_duplicates().values.tolist()
  header_list = totalData.columns.values.tolist()
  group=list()
  for tab in tabs:
    tabData=totalData[totalData['Library Name'] == tab]
    tabData=tabData.drop('Library Name', axis=1)
    tabData=tabData.values.tolist()
    tabLayout=[[sg.Table(values=tabData,  headings=header_list[1:], display_row_numbers=False, justification='left', auto_size_columns=True, background_color='white', alternating_row_color='lightgrey', num_rows=min(25,len(totalData)))]]
    group.append([sg.Tab(tab, tabLayout)])
    
  
  layout=[[sg.TabGroup(group)], [sg.Button("OK")]]
  win = sg.Window("Details", location=LOCATION)
  win.Layout(layout)
  while True:
    ev, values = win.Read()
    if ev is "OK" or ev == 'exit':  
      win.Close()  
      home.UnHide()
      return "" 


def selectAllLibraries(ev, home):
  if ev is "selectAllLibs":
    for lib in os.listdir(str(PATH_LIBS)):
      if lib.endswith(".xml"):
        home.FindElement(lib.replace(".xml", "")).Update(True)

def selectAllProducts(ev, home):
  if ev is "selectAllProducts":
    for lib in os.listdir(str(PATH_TEMPLATES)):
      if lib.endswith(".xml"):
        home.FindElement(lib.replace(".xml", "")).Update(True)

def selectAllExcels(ev, home):
  if ev is "selectAllFiles":
    for lib in os.listdir(str(PATH_EXCELS)):
      home.FindElement(lib).Update(True)

def deSelectAllExcels(home):
  for lib in os.listdir(str(PATH_EXCELS)):
    home.FindElement(lib).Update(False)

def deSelectAllLibraries(home):
  for lib in os.listdir(str(PATH_LIBS)):
    if lib.endswith(".xml"):
      home.FindElement(lib.replace(".xml", "")).Update(False)

def deSelectAllProducts(home):
  for lib in os.listdir(str(PATH_TEMPLATES)):
    if lib.endswith(".xml"):
      home.FindElement(lib.replace(".xml", "")).Update(False)

def getValueOfOptions(selectedOption):
  parts=""
  if selectedOption != "":
    if selectedOption == 'Risk patterns & Rules':
      parts=""
    if selectedOption == 'Risk patterns':
      parts="riskPatterns"
    if selectedOption == 'Rules':
      parts="rules"
  return parts

def getSelectedLibs(values, files):
  for lib in os.listdir(str(PATH_LIBS)):
    if lib.endswith(".xml"):
      if values[lib.replace(".xml","")]:
        files.append(PATH_LIBS / lib)
  return files

def getSelectedProducts(values, files):
  for lib in os.listdir(str(PATH_TEMPLATES)):
    if lib.endswith(".xml"):
      if values[lib.replace(".xml","")]:
        files.append(PATH_TEMPLATES / lib)
  return files

def getSelectedExcels(values, files):
  for file in os.listdir(str(PATH_EXCELS)):
    if values[file]:
      files.append(PATH_EXCELS / file)
  return files

def getSelectedData(values, files):
  normalChangeLog = False
  if values['fileOldLibraryInput'] != '' and values['fileNewLibraryInput'] != '':
    files.append(values['fileOldLibraryInput'])
    files.append(values['fileNewLibraryInput'])
  else:
    normalChangeLog = True
  
  return files, normalChangeLog

def showMainFrame(home):
  home.FindElement("frameUpgrade").Update(visible=False)
  home.FindElement("frameLibs").Update(visible=False)
  home.FindElement("frameProducts").Update(visible=False)
  home.FindElement("frameExcels").Update(visible=False)
  home.FindElement("options").Update(visible=False)
  home.FindElement("standards").Update(visible=False)
  home.FindElement("serverConfig").Update(visible=False)
  home.FindElement("frameResults").Update(visible=False)
  home.FindElement("mainFrame").Update(visible=True)
  home.FindElement("buttons").Update(visible=False)
  home.FindElement("changeLogFrame").Update(visible=False)
  home.FindElement("exit").Update(visible=True)

def getCommandOS():
  command=""
  if sys.platform == 'darwin':
    command = 'open'
  elif sys.platform == 'linux':
     command = 'nautilus'
  elif sys.platform == 'win32':
    command = 'start'
  return command

def selectionWindow(title, home, showChangeLogOptions=False, showOptions=False, showStandards=False, showServerConfig=False, showExcelOptions=False, showExistingStandards=False, showUpgrade=False, showProductOptions=False):
  data=Data()
  data.normalChangeLog = False

  home.FindElement("frameLibs").Update(visible=True)
  home.FindElement("mainFrame").Update(visible=False)
  home.FindElement("existingStandards").Update(visible=False)
  home.FindElement("buttons").Update(visible=True)
  home.FindElement("exit").Update(visible=False)
  if showProductOptions:
    home.FindElement("frameLibs").Update(visible=False)
    home.FindElement("frameProducts").Update(visible=True)
  if showUpgrade:
    home.FindElement("frameUpgrade").Update(visible=True)
    home.FindElement("frameLibs").Update(visible=False)
    home.FindElement("frameExcels").Update(visible=False)
  if showOptions:
    home.FindElement("options").Update(visible=True)
  if showStandards:
    home.FindElement("standards").Update(visible=True)
  if showServerConfig:
    home.FindElement("serverConfig").Update(visible=True)
  if showExcelOptions:
    home.FindElement("frameExcels").Update(visible=True)
    home.FindElement("frameLibs").Update(visible=False)
    home.FindElement("frameUpgrade").Update(visible=False)
  if showExistingStandards:
    home.FindElement("existingStandards").Update(visible=True)
  if showChangeLogOptions:
    home.FindElement("frameLibs").Update(visible=False)
    home.FindElement("changeLogFrame").Update(visible=True)
  startProgressBar(home)
    
  data.files=list()
  
  while True:    
    ev, values = home.Read() 
    selectAllLibraries(ev, home)
    selectAllProducts(ev, home)
    selectAllExcels(ev, home)
    checkConnection(ev, home, values)
    if ev is "cancel" or ev == 'exit':
      home.FindElement('fileBrowseValue').update('')
      home.FindElement('fileBrowseValueProduct').update('')
      home.FindElement('fileBrowseValueExcel').update('')
      showMainFrame(home)
      return Data()

    if ev is 'showFolderLastRelease':
      try:
        os.system('%s %s &'%(getCommandOS(), str(Path.cwd() / "inputFiles" / "lastRelease")))
      except:
        logger.info("The File Browse is not been able to open")
    
    if ev is 'showFolderCurrentRelease':
      try:
        os.system('%s %s &'%(getCommandOS(),str(Path.cwd() / "inputFiles" / "currentRelease")))
      except:
        logger.info("The File Browse is not been able to open")
     
    if ev is "submit":
      progressBar(home)
      home.Refresh()
      #input("Press Enter to continue...")
      data.libraryMaster = values['libraryMaster']
      data.libraryNewVersion = values['libraryNewVersion']
      data.parts=getValueOfOptions(values['comboOptions'])
      if showStandards:
        data.parts=values['comboStandards']
      data.files=getSelectedLibs(values, data.files)
      if showExcelOptions:
        data.files=getSelectedExcels(values, data.files)
      if showChangeLogOptions:
        data.files, data.normalChangeLog =getSelectedData(values, data.files)
      if showProductOptions:
        data.files=getSelectedProducts(values, data.files)
      if showExistingStandards:
        data.selectedStandard_path = values['comboExistingStandards']
      if home.FindElement('fileBrowseValueExcel').Get() != "":
        data.files.append(Path(home.FindElement('fileBrowseValueExcel').Get()))
        home.FindElement('fileBrowseValueExcel').update('')
      if home.FindElement('fileBrowseValue').Get() != "":
        data.files.append(Path(home.FindElement('fileBrowseValue').Get()))
        home.FindElement('fileBrowseValue').update('')
      if home.FindElement('fileBrowseValueProduct').Get() != "":
        data.files.append(Path(home.FindElement('fileBrowseValueProduct').Get()))
        home.FindElement('fileBrowseValueProduct').update('')

      if values['apiToken'] != "" and values['urlServer'] != "":
        data.serverUrl=values['urlServer']
        data.apiToken=values['apiToken']
        writeConfig(data.serverUrl, data.apiToken)

      deSelectAllProducts(home)
      deSelectAllLibraries(home)
      deSelectAllExcels(home)
      showMainFrame(home)

      return data



def checkIfJoinMethod(event, results, home, links):  
  if event == "1. Join library from several files":    
    data=selectionWindow(
      title="Select the library or libraries to join in a file:",
      showOptions=True,
      home=home)
    
    for file in data.files:
      if file.name.endswith(".xml"):
        results, output_path=joinFiles(Path.cwd() / "outFiles" / "separatedLibraries" / file.name.replace(".xml", ""), "") 
        links.append(output_path)
  return results, links

def checkIfSeparateMethod(event, results, home, links):
  if event == "2. Separate library in several files":    
    libArray=list()
    data=selectionWindow(
          title="Select the library or libraries to separate in several files and folders:", 
          showOptions=True,
          home=home)   
    option = data.parts
    for file in data.files:
      results+=separateFiles(
        folder=Path.cwd() / "outFiles" / "separatedLibraries" / file.name.replace(".xml", ""),
        library_path=Path.cwd() / "libraries" / file, 
        parts=option)          
  return results, links

def checkIfConvertXmlToExcel(event, results, home, links):
  if event == "3. Convert XML file to Excel file": 
    startProgressBar(home)
    libArray=list()
    for lib in os.listdir(str(Path.cwd() / "libraries")):
      if lib.endswith(".xml"):
        libArray.append(lib)    
    data=selectionWindow(
      title="Select the library or libraries to generate the Excel file:", 
      home=home)   
    
    for file in data.files:
      if file.name.endswith(".xml"):
        excelPath=Path.cwd() / "outFiles" / "spreadSheets" / str(file.name.replace(".xml",".xlsx"))
        link=convertXmlToExcel(
          xmlPath= file,
          excelPath=excelPath)
        results+="Library '%s' was converted to Excel file successfully and the output file is in the path '%s'.\n"%(str(file.name), Path.cwd() / "outFiles" / "spreadSheets" / file.name.replace(".xml",".xlsx"))
        links.append(link)
      else:
        results+="File '%s' is not converted, because its extension is wrong"%file

  return results, links

def checkIfConvertExcelToXml(event, results, home, links):
  if event == "4. Convert Excel file to XML file" :       
    data=selectionWindow(
      title="Select the library or libraries to generate the XML file:", 
      showExcelOptions=True,
      home=home)   
    for file in data.files:
      if file.name.endswith(".xlsx"):
        results+=convertExcelToXml(excelFilePath=Path.cwd() / "inputFiles" / "spreadSheetFiles" / file)
        links.append(Path.cwd() / "outFiles" / "outputLibs" / file.name.replace(".xlsx", ".xml"))
      else:
        results+="File '%s' is not converted, because its extension is wrong"%file

  return results, links

def checkIfConvertXmlToHtml(event, results, home, links):
  if event == "5. Generate HTML file from XML file" : 
    libArray=list()
    for lib in os.listdir(str(Path.cwd() / "libraries")):
      if lib.endswith(".xml"):
        libArray.append(lib)    
    data=selectionWindow(
      title="Select the library or libraries to generate the HTML file:", 
      home=home)  
        
    for file in data.files:
      if file.name.endswith(".xml"):
        generateHTML(
          xml_path=Path.cwd() / "libraries" / file, 
          html_path=Path.cwd() / "outFiles" / "generatedHtml" / file.name.replace(".xml",".html"))
        results+="Library '%s' was converted to HTML file successfully and the output file is in the path '%s'.\n"%(file.name.replace(".xml",""), Path.cwd() / "outFiles" / "generatedHtml" / file.name.replace(".xml",".html"))
        links.append(Path.cwd() / "outFiles" / "generatedHtml" / file.name.replace(".xml",".html"))
      else:
        results+="File HTML '%s' is not generated, because its extension is wrong"%file
  return results, links

def checkIfLibraryDetails(event, results, home, links):
  if event == "6. Show library details" :  
    libs_path = Path.cwd() / "libraries"
    libs=list()
    for lib in os.listdir(str(libs_path)):
      if lib.endswith(".xml"):
        libs.append(lib)
    data=selectionWindow(
      title="Select the library or libraries to show the library details:",
      home=home)
    
    columns=['Library Name', 'Risk Pattern', '# Use Cases', '# Threats', '# Weaknesses', '# Countermeasures']
    totalData=pd.DataFrame([], columns=columns)
    for file in data.files:
      if file.name.endswith(".xml"):
        data=readInfoFromXml(libs_path / file, columns)
        totalData=totalData.append(data)
        results+="The details of the library '%s' are shown in other window.\n"%file.name.replace(".xml","")
      else:
        results+="Details from file '%s' are not shown, because its extension is wrong.\n"%file.name.replace(".xml","")
    showDetails(totalData, home)
        
  return results, links

def checkIfThreatMitigationTest(event, results, home, links):
  if event == "7. Check the threat mitigation of a library" :
    libs=list()
    path_libs=Path.cwd() / "libraries"
    for lib in os.listdir(str(path_libs)):
      if lib.endswith(".xml"):
        libs.append(lib)
    data=selectionWindow(
      title="Select the library or libraries to test the threat mitigation:",
      home=home)
    
    with open(str(Path.cwd() / "inputFiles" / "yamlFiles" / "threatMitigationExceptions.yaml"), 'r') as stream:
      dataExt=yaml.safe_load(stream) 
    for file in data.files:
      if file.name.endswith(".xml"):
        try:
          exceptions=dataExt['exceptions'][0][file.replace(".xml","")]
        except:
          exceptions=[]
        text=libMitigationTest(str(Path.cwd() / "libraries" / file), exceptions)
        if text == "" and len(exceptions) != 0:
          excepts=list()
          for row in exceptions:
            excepts.append(row[1])
          text+="The library file '%s' passed all threat mitigation tests without error.But with exceptions in the following threats: %s.\n"%(file, str(excepts).replace("[","").replace("]",""))
        if text == "" and len(exceptions) == 0:
          text="The library file '%s' passed all threat mitigation tests without error.\n"%file
        results+=text
      else:
        results+="Threat mitigation form file '%s' is not checked, because its extension is wrong"%file
  return results, links

def checkIfChangeLog(event, results, home, links):
  outFiles=""
  if event == "8. Generate the ChangeLog file from two versions" :
    data=selectionWindow(
      title="Select the library or libraries to generate the XML file:", 
      showChangeLogOptions=True,
      home=home)
    if data.normalChangeLog == True:
      results, outFiles=generateChangeLog([])
      currentData, oldData, results=getInfoFromChangeLog([])
      showDetailsChangeLog(currentData, oldData, home)
      links.append(outFiles)
    if data.normalChangeLog == False:
      results, outFiles=generateChangeLog(data.files)
      currentData, oldData, results=getInfoFromChangeLog(data.files)
      showDetailsChangeLog(currentData, oldData, home)
      links.append(outFiles)

  return results, links

def checkIfAddStandardToLibrary(event, results, home, links):
  # select library with options (standard from a list)
  if event == "9. Add Standard to library or libraries":
    libs=list()
    libs_path=Path.cwd() / "libraries"
    for lib in os.listdir(str(libs_path)):
      if lib.endswith(".xml"):
        libs.append(lib)
    options=list()
    data=selectionWindow(
      title="Select the library or libraries to add the selected standard:", 
      showStandards=True,
      home=home)    
    
    option = data.parts
    for file in data.files:
      if file.name.endswith(".xml"):    
        standard_path_csv=Path.cwd() / "inputFiles" / "standardsFiles" / str(option)
        path_library=Path.cwd() / "libraries" / file
        results+=addStandardToLibrary(standard_path_csv, path_library, option)
        links.append(path_library)
      else:
        results+="The standard is not added to file '%s' , because its extension is wrong"%file
  return results, links

def checkIfUgradeLibraryFromOtherFile(event, results, home, links):
  path_new_library=Path.cwd() / "inputFiles" / "libsToMerge"
  if event == "10. Upgrade a library with other version of the same library":
    path_library=Path.cwd() / "libraries"
    libArray=list()
    for lib in os.listdir(str(path_library)):
      if lib.endswith(".xml"):
        libArray.append(lib)    
    data=selectionWindow("Select the main library and the secondary library to upgrade it:",showUpgrade=True, home=home)
    
    if str(data.libraryMaster)!="" and str(data.libraryNewVersion)!="":
      results=mergeLibrariesByPaths(path_library / str(data.libraryMaster+".xml") , path_new_library / str(data.libraryNewVersion + ".xml"))
    links.append(path_new_library / str(data.libraryNewVersion + ".xml"))
  return results, links

def checkIfGenerateHtmlFileWithStandardsVsCountermeasures(event, results, home, links):
  if event == "11. Generate HTML file with the relationships between a standard and the countermeasures":

    data =selectionWindow(
      "Select the standard to generate the HTML file:", 
      showExistingStandards=True,
      home=home)
    
    if data.selectedStandard_path != "":
      path=Path.cwd() / "inputFiles" / "descriptionOfStandards"
      results, output_path=generateHtmlFromLibrariesAndStandard(path / str("standard_"+data.selectedStandard_path + "_info.csv"), data.files)
      links.append(output_path)
  return results, links

def checkIfUploadLibrariesToServer(event, results, home, links):
  if event == "12. Upload the selected libraries to the configured server":
    data=selectionWindow(
      title="Select the library or libraries to test the threat mitigation:",
      showServerConfig=True,
      home=home)
    for file in data.files:
      removeLibraryByApi(PATH_LIBS / file, data.serverUrl, data.apiToken)
    
    for file in data.files:
      results+=uploadLibraryByApi(PATH_LIBS / file, data.serverUrl, data.apiToken)

  return results, links

def checkIfAddReferencesFromExcel(event, results, home, links):
  files = []
  excels_path = Path.cwd() / "inputFiles" / "externalSpreadsheets"
  if event == "13. Add control references using the mapping from Excel file":
    files += [each for each in os.listdir(str(excels_path)) if each.endswith('.xlsx')]
    excelFile, replaceLibs = selectionOfExcelFile("Generate the libraries with the new references in the countermeasures", files, excels_path, home)
    
    if excelFile != "":      
      results+=addReferencesToLibrariesByExcelFile(excels_path / excelFile, replaceLibs, excelFile)
  
  return results, links

def checkIfConvertRulesFromExcelToXML(event, results, home, links):
  files = []
  excels_path = Path.cwd() / "inputFiles" / "externalSpreadsheets" / "rulesEditor"
  if event == "14. Convert Rules from Excel file to XML file" :       
    files += [each for each in os.listdir(str(excels_path)) if each.endswith('.xlsx')]
    excelFile = selectionOfExcelRulesFile("Select the Rules Editor Excel utility file", files, excels_path, home)

    if excelFile != "":
      results+=convertRulesFromExcelToXML(excels_path / excelFile)
      links.append(Path.cwd() / "outFiles" / "rulesEditorLibraries" / excelFile.replace(".xlsx", ".xml"))

  return results, links

def checkIfRiskFromXML(event, results, home, links):
  if event == "15. Show risk calculation from XML product file":
    startProgressBar(home)
    productArray = list()
    for product in os.listdir(str(Path.cwd() / "products")):
      if product.endswith(".xml"):
        productArray.append(product)
    data = selectionWindow(
      title="Select the product or products to show risk calculation:",
      showProductOptions=True,
      home=home)

    for file in data.files:
      if file.name.endswith(".xml"):
        htmlPath = Path.cwd() / "outFiles" / "generatedHtml" / str(file.name.replace(".xml", ".html"))
        link = calculateRiskToHTML(
          xmlPath=file,
          htmlPath=htmlPath)
        results += "Risk was calculated for product '%s' successfully and the output file is in the path '%s'.\n" % (
        str(file.name), Path.cwd() / "outFiles" / "generatedHtml" / file.name.replace(".xml", ".html"))
        links.append(link)

      else:
        results += "Risk is not calculated for '%s' because its extension is wrong" % file
  return results, links

def loadMainLayout():
  layout = [
          [sg.Button("1. Join library from several files", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("2. Separate library in several files", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("3. Convert XML file to Excel file", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("4. Convert Excel file to XML file", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("5. Generate HTML file from XML file", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("6. Show library details", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("7. Check the threat mitigation of a library", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("8. Generate the ChangeLog file from two versions", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("9. Add Standard to library or libraries", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("10. Upgrade a library with other version of the same library", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("11. Generate HTML file with the relationships between a standard and the countermeasures", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("12. Upload the selected libraries to the configured server", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("13. Add control references using the mapping from Excel file", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("14. Convert Rules from Excel file to XML file", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],
          [sg.Button("15. Show risk calculation from XML product file", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)],

  ]
  return layout


def main():
  print('starting up...') # Seems to help repl.it
  logger.info("App UI launched")
  sg.SetOptions(element_padding=(10, 3), auto_size_buttons=True, margins=(4,4), text_justification='Left', background_color='#e1e1e1', element_background_color='#e1e1e1', text_element_background_color='#e1e1e1', icon=str(Path.cwd() / "inputFiles" / "IriusRiskToolKitUI_icon.ICO"))

  layout = loadMainLayout()
  layoutLibs=getLayoutLibs()
  layoutProducts=getLayoutProducts()
  layoutExcels=getLayoutExcels()
  layoutUpgrade=getLayoutUpgrade()
  changeLogLayout = getChangeLogLayout()
  layoutResults=[[]]

  mainLayout=[[
    sg.Frame("Select the action to do:", layout, key='mainFrame'), 
    sg.Frame("Select the libraries to use:", layoutLibs, key='frameLibs', visible=False),
    sg.Frame("Select the products to use:", layoutProducts, key='frameProducts', visible=False),
    sg.Frame("Select the Excels to use:", layoutExcels, key='frameExcels', visible=False),
    sg.Frame("Upgrading library:", layoutUpgrade, key='frameUpgrade', visible=False),
    sg.Frame("Select libraries to generate the ChangeLog:", changeLogLayout, key='changeLogFrame', visible=False),
    sg.Frame("Results:", layoutResults, key='frameResults', visible=False)],
    [sg.Frame("", [[sg.Text("Ready!", size=SIZE_ELEMENT, key='progbar', text_color='white', background_color='royal blue', justification='center')]], key='status', visible=True)],
    [sg.Frame("", [[sg.Button("Submit", key='submit'), sg.Button("Cancel",key='cancel')]], key='buttons', visible=False)], [sg.Button('Exit', key='exit')]
  ]
  home = sg.Window('IriusRiskToolKitUI', mainLayout, location=LOCATION, auto_size_text=True)
  
  while True:
    results="" 
    event, vals1 = home.Read() 
    if event != None and event != "":
      logger.info("Event '%s' is selected."%event)
    if (event == "exit") or (event == None): 
      break
    showMainFrame(home)
    links=list()
    results, links=checkIfJoinMethod(event, results, home, links)
    results, links=checkIfSeparateMethod(event, results, home, links)
    results, links=checkIfConvertXmlToExcel(event, results, home, links)
    results, links=checkIfConvertExcelToXml(event, results, home, links)
    results, links=checkIfConvertXmlToHtml(event, results, home, links)
    results, links=checkIfLibraryDetails(event, results, home, links)
    results, links=checkIfThreatMitigationTest(event, results, home, links)
    results, links=checkIfChangeLog(event, results, home, links)
    results, links=checkIfAddStandardToLibrary(event, results, home, links) 
    results, links=checkIfUgradeLibraryFromOtherFile(event, results, home, links)
    results, links=checkIfGenerateHtmlFileWithStandardsVsCountermeasures(event, results, home, links)
    results, links=checkIfUploadLibrariesToServer(event, results, home, links)
    results, links=checkIfAddReferencesFromExcel(event, results, home, links)
    results, links=checkIfConvertRulesFromExcelToXML(event, results, home, links)
    results, links=checkIfRiskFromXML(event, results, home, links)
    
    finishProgressBar(home)
    logger.info("Results page is shown.")
    showLinks(links, results, home)
    startProgressBar(home)

  home.Close()


if __name__ == '__main__':
  main()
