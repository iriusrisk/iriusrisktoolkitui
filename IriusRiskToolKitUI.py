import subprocess
import webbrowser
import PySimpleGUI as sg
import pandas as pd
from src.addReferencesFromExcel import addReferencesToLibrariesByExcelFile
from src.addStandardtoLibraries import getStandards, setStandard
from src.common import readConfig, writeConfig, testConnection
from src.convertExcelToXml import convertExcelToXml
from src.convertExcelToXml import convertRulesFromExcelToXML
from src.convertXmlToExcel import convertXmlToExcel
from src.convertXmlToHtmlFile import generateHTML
from src.createLibraryFromDefaultOne import createLibraryFromDefaultOne
from src.generateChangeLogFromVersions import generateChangeLog
from src.generateHtmlStandardvsCountermeasures import generateHtmlFromLibrariesAndStandard
from src.generateRulesHtml import generateRulesHtml
from src.generateRulesHtml import questions
from src.libraryDetails import readInfoFromXml
from src.mergeLibraries import mergeLibrariesByPaths
from src.riskCalculator import calculateRiskToHTML
from src.updateServerWithCloudComponents import *
from src.common import isExcelFile
from src.pytestgui.view import MainWindow
from src.pytestgui.model import UnittestProject

try:
    from Tkinter import *
except ImportError:
    from tkinter import *


toolkitVersion = "Version 1.1"

options = [
    "Convert XML file to Excel file",
    "Convert Excel file to XML file",
    "Generate HTML file from XML file",
    "Show library details",
    "Generate the ChangeLog file from two versions",
    "Add Standard to library or libraries",
    "Upgrade a library with other version of the same library",
    "Generate HTML file with the relationships between a standard and the countermeasures",
    "Upload the selected libraries to the configured server",
    "Add control references using the mapping from Excel file",
    "Convert Rules from Excel file to XML file",
    "Show risk calculation from XML product file",
    "Questions about rules",
    "Create a new library from a default one",
    "Run tests for libraries"
]

LOCATION = (0, 0)
SIZE_ELEMENT = (100, 1)

# Create and configure logger
# filemode = 'w' that will change the mode of operation from "append" to "write"
# and will overwrite the file every time we run our application
logging.basicConfig(filename="logFile.log",
                    format='%(asctime)s  %(levelname)-10s %(message)s',
                    datefmt="%Y-%m-%d-%H-%M-%S",
                    filemode='w')

# Creating an object
logger = logging.getLogger()

# Setting the threshold of logger to INFO
logger.setLevel(logging.INFO)

# So that it does not complain about the Look and Feel in Windows
sg.change_look_and_feel('DefaultNoMoreNagging')

# BUTTON_COLOR=('white', '#424632')
BUTTON_COLOR = ('black', '#f2f2f2')
PATH_LIBS = Path.cwd() / "libraries"
PATH_TEMPLATES = Path.cwd() / "products"
PATH_EXCELS = Path.cwd() / "inputFiles" / "spreadSheetFiles"


def selectionOfExcelFile(title, files, mainPath, home):
    home.hide()
    mainRelativ = str(mainPath).replace(str(Path.cwd()), "..")
    libraries_path = Path.cwd() / "libraries"
    layout = [
        [sg.Text(title)],
        [sg.Text("Select the Excel file (Working directory: '%s'):" % mainRelativ), sg.InputCombo(files)],
        [sg.Text("Do you want to replace the libraries in the directory '%s'?" % libraries_path), sg.Checkbox(text='')],
        [sg.Submit(), sg.Cancel()]
    ]
    win = sg.Window(title, layout, location=LOCATION)
    win.un_hide()
    while True:
        ev, values = win.read()
        if ev == "Cancel" or ev == 'Exit':
            win.close()
            home.un_hide()
            return "", ""
        if ev == "Submit":
            win.close()
            home.un_hide()
            return values[0], values[1]


def selectionOfExcelRulesFile(title, files, mainPath, home):
    home.hide()
    mainRelativ = str(mainPath).replace(str(Path.cwd()), "..")
    libraries_path = Path.cwd() / "outFiles" / "rulesEditorLibraries"
    layout = [
        [sg.Text(title)],
        [sg.Text("Select the Excel file (Working directory: '%s'):" % mainRelativ), sg.InputCombo(files)],
        [sg.Submit(), sg.Cancel()]
    ]
    win = sg.Window(title, layout, location=LOCATION)
    win.un_hide()
    while True:
        ev, values = win.read()
        if ev == "Cancel" or ev == 'Exit':
            win.close()
            home.un_hide()
            return ""
        if ev == "Submit":
            win.close()
            home.un_hide()
            return values[0]


def startProgressBar(home):
    home['progbar'].update("Ready!", text_color='white', background_color='royal blue')


def progressBar(home):
    home['progbar'].update("Loading ...", text_color='white', background_color='DarkOrange3')

def progressBarTest(home, name):
    home['progbar'].update(f"Loading {name} tests", text_color='white', background_color='DarkOrange3')

def finishProgressBar(home):
    home['progbar'].update("Done", text_color='white', background_color='green')


class Data:
    def __init__(self):
        self.files = []
        self.apitoken = ""
        self.serverUrl = ""
        self.selectedStandard_path = ""
        self.parts = ""
        self.libraryMaster = ""
        self.libraryNewVersion = ""
        self.normalChangeLog = ""
        self.filename = ""
        self.name = ""
        self.ref = ""
        self.userWantsASVS3 = False
        self.cancel = False


def getChangeLogLayout():
    files = [
        [sg.Text(
            "You can generate the Change Log for all libraries from the following paths (by default, you shall not select any file):")],
        [sg.Text(" - Old release ('/inputFiles/oldRelease) "),
         sg.Button("Folder Old Release", key='showFolderOldRelease', button_color=BUTTON_COLOR)],
        [sg.Text(" - Updated release ('/inputFiles/updatedRelease) "),
         sg.Button("Folder Updated Release", key='showFolderUpdatedRelease', button_color=BUTTON_COLOR)],
        [sg.Text("Or generate the Change Log from two files (if the following File Browse are filled:")],
        [sg.Text('Select the old library:'), sg.Input(key='fileOldLibraryInput'),
         sg.FileBrowse(key='fileOldLibrary', button_color=BUTTON_COLOR)],
        [sg.Text('Select the updated library:'), sg.Input(key='fileUpdatedLibraryInput'),
         sg.FileBrowse(key='fileUpdatedLibrary', button_color=BUTTON_COLOR)]
    ]
    return files


def getStandardsLayout():
    radio_choices = ['Export standards to CSV', 'Add standards to library using CSV',
                     'Delete standards from library using CSV']
    radio_keys = ['exportStandard', 'addStandard', 'deleteStandard']

    radio = []
    for i in range(0, len(radio_choices)):
        radio.append([sg.Radio(radio_choices[i], 1, key=radio_keys[i])])

    files = [
        [sg.Text(
            "You can export all standards from a library to a CSV file (Default: ./inputFiles/standardsFiles/standardEditor.csv):")],
        [sg.Text('Select CSV (optional):'), sg.Input(key='fileCSVInputStandard'),
         sg.FileBrowse(key='fileCSVStandard', button_color=BUTTON_COLOR)],
        [sg.Text('Select the library to work with:'), sg.Input(key='fileLibraryInputStandard'),
         sg.FileBrowse(key='fileLibraryStandard', button_color=BUTTON_COLOR)],
        [sg.Text('Select what to do:')],
    ]
    files = files + radio
    return files


def getLayoutExcels():
    files = list()

    for excel in os.listdir(str(PATH_EXCELS)):
        if isExcelFile(excel):
            files.append([sg.Checkbox(excel, key=excel, default=False)])

    files.append([sg.Button("Select all files", key='selectAllFiles', button_color=BUTTON_COLOR)])
    files.append([sg.Text('Filename:'), sg.Input(key='fileBrowseValueExcel'), sg.FileBrowse(key='browseExcel')])

    layout = [
        [sg.Frame("Select the Excel file to convert in XML (working directory: '../inputFiles/spreadSheetFiles/'):",
                  files, key='excels')]
    ]
    return layout


def getLayoutUpgrade():
    path = Path.cwd() / "inputFiles" / "libsToMerge"
    mainRelativ = str(PATH_LIBS).replace(str(Path.cwd()), "..")
    secRelativ = str(path).replace(str(Path.cwd()), "..")
    arrayMaster = list()
    for lib in os.listdir(str(PATH_LIBS)):
        if lib.endswith(".xml"):
            arrayMaster.append(lib.replace(".xml", ""))

    arrayNewLibraries = list()
    for lib in os.listdir(str(path)):
        if lib.endswith(".xml"):
            arrayNewLibraries.append(lib.replace(".xml", ""))

    layout = [
        [sg.Text("Select the main library (Working directory: '%s'):" % mainRelativ),
         sg.InputCombo(arrayMaster, key='libraryMaster')],
        [sg.Text("Select the second library (Working directory: '%s'):" % secRelativ),
         sg.InputCombo(arrayNewLibraries, key='libraryNewVersion')]
    ]
    return layout


def getLayoutNewCopy():
    layout = [
        [sg.Text('Select the base library:'), sg.Input(key='newCopyLibraryInput'),
         sg.FileBrowse(key='newCopyLibraryBrowse')],
        [sg.Text('Library filename (*.xml):'), sg.Input(key='newCopyLibraryFileName')],
        [sg.Text('Library name:'), sg.Input(key='newCopyLibraryName')],
        [sg.Text('Library ref:'), sg.Input(key='newCopyLibraryRef')],
        [sg.Checkbox("Do you want ASVS3 instead of ASVS4 countermeasures?", key="checkboxNewCopy", default=False)]
    ]
    return layout


def getLayoutLibs():
    libs = list()
    libsPath = list()
    for lib in os.listdir(str(PATH_LIBS)):
        if lib.endswith(".xml"):
            libsPath.append(Path.cwd() / "libraries" / lib)
            libs.append([sg.Checkbox(lib.replace(".xml", ""), key=lib.replace(".xml", ""), default=False)])

    riskPatterns = set()
    for path in libsPath:
        root = etree.parse(str(path)).getroot()
        for riskPattern in root.find("components").iter("component"):
            riskPatterns.add(riskPattern.attrib['ref'])

    libs.append([sg.Button("Select all libraries", key='selectAllLibs', button_color=BUTTON_COLOR)])
    libs.append([sg.Text('Filename:'), sg.Input(key='fileBrowseValue'), sg.FileBrowse(key='browse')])
    standardList = os.listdir(str(Path.cwd() / "inputFiles" / "standardsFiles"))
    standards = [
        [sg.Text("Select the option:", key='textStandards'), sg.InputCombo(standardList, key='comboStandards')]]
    options = [[sg.Text("Select the option:", key='textOptions'),
                sg.InputCombo(['Risk patterns & Rules', 'Risk patterns', 'Rules'], key='comboOptions')]]
    questionCombo = [[sg.Text("Select the question:", key='textQuestion'),
                      sg.InputCombo(list(questions.values()), key='comboQuestions')],
                     [sg.Text("Write QuestionID/ref/name:", key='textValue'),
                      sg.Input(key="textValueQuestion"),
                      sg.Text("Select risk pattern:", key='textRiskPattern'),
                      sg.InputCombo(sorted(riskPatterns, key=str.lower), key='comboRiskPatterns', size=(30, 30))],
                     [sg.Button("Load risk patterns from uploaded library only", key="loadRiskPatterns")]]

    existingStandardList = list()
    path_info_standards = Path.cwd() / "inputFiles" / "descriptionOfStandards"
    for i in os.listdir(str(path_info_standards)):
        existingStandardList.append(i.replace("standard_", "").replace("_info.csv", ""))
    existingStandards = [[sg.Text("Select the standard:", key='textExistingStandards'),
                          sg.InputCombo(existingStandardList, key='comboExistingStandards')]]

    serverUrl, apiToken, errorMessage = readConfig()
    serverConfig = [
        [sg.Text("Server configurations:")],
        [sg.Text("Server url:"), sg.InputText(serverUrl, key='urlServer')],
        [sg.Text("Api Token:"), sg.InputText(apiToken, key='apiToken')],
        [sg.Button("Test Connection", key='test-connection')],
        [sg.Text("Error message:"), sg.InputText(errorMessage, key='errorMessage')]
    ]

    layout = [
        [sg.Frame("Select the library or libraries to use (working directory: '../libraries/'):", libs, key='libs'),
         sg.Frame("Options:", options, key='options'),
         sg.Frame("Questions:", questionCombo, key='frameQuestion'),
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
        [sg.Frame("Select the product or products to use (working directory: '../products/'):", products,
                  key='products'),
         sg.Text("Don't forget to update configuration values (weights, trustzones, etc.) in src/riskCalculator.py")]
    ]

    return layout


def checkConnection(ev, home, values):
    if ev == "test-connection":
        msg = testConnection(values['urlServer'], values['apiToken'])
        home["errorMessage"].update(msg)


def showLinks(links, results, home):
    if len(links) > 0 or results != "":
        home.hide()
        layout = list()
        for link in links:
            extensions = [".html", ".csv", ".xlsx", ".xls"]
            if any([str(link).endswith(ext) for ext in extensions]):
                layout.append([
                    sg.Text(link.name, size=(30, 1)),
                    sg.Button('Open', key='open' + str(link), button_color=BUTTON_COLOR, size=(5, 1))
                ])

        lay = [[sg.Frame("Results", [[sg.Multiline(results, size=(100, 25))]])],
               [sg.Frame("Links to be opened", layout)],
               [sg.Button("Ok")]
               ]
        win = sg.Window("Details", location=LOCATION)
        win.layout(lay)
        while True:
            ev, values = win.read()
            if ev == "Ok" or ev == 'exit':
                win.close()
                home.un_hide()
                return ""

            else:
                if ev.startswith("open"):
                    ev = Path(ev[4:])
                    if ev in links:
                        if ev.suffix == ".html":
                            webbrowser.open('file://' + str(links[links.index(ev)]))
                        if ev.suffix in [".xlsx", ".xls", ".csv"]:
                            try:
                                subprocess.Popen("start \"excel.exe\" '%s'" % str(ev))
                            except:
                                try:
                                    subprocess.Popen('libreoffice \"' + str(ev) + '\"', shell=True)
                                except:
                                    try:
                                        subprocess.Popen("libreoffice.exe", str(ev), shell=True)
                                    except:
                                        sg.popup("We cannot find the program to open the Excel File.")


def showDetailsChangeLog(updatedData, oldData, home):
    tabs = updatedData['Library Name'].drop_duplicates().values.tolist()
    header_list = updatedData.columns.values.tolist()
    group = list()
    for tab in tabs:
        tabData1 = updatedData[updatedData['Library Name'] == tab]
        tabData1 = tabData1.drop('Library Name', axis=1)
        tabData1 = tabData1.values.tolist()

        tabData2 = oldData[oldData['Library Name'] == tab]
        tabData2 = tabData2.drop('Library Name', axis=1)
        tabData2 = tabData2.values.tolist()
        if not tabData2:
            tabLayout = [[
                sg.Table(values=tabData1, headings=header_list[1:], display_row_numbers=False, justification='left',
                         auto_size_columns=True, background_color='white', alternating_row_color='lightgrey',
                         num_rows=min(25, len(updatedData)))]
            ]
        else:
            tabLayout = [
                [sg.Text("Updated Version", size=(96, 1), justification='left'),
                 sg.Text("Old Version", size=(100, 1), justification='left')],
                [
                    sg.Table(values=tabData1, headings=header_list[1:], display_row_numbers=False, justification='left',
                             auto_size_columns=True, background_color='white', alternating_row_color='lightgrey',
                             num_rows=min(25, len(updatedData))),
                    sg.Table(values=tabData2, headings=header_list[1:], display_row_numbers=False, justification='left',
                             auto_size_columns=True, background_color='white', alternating_row_color='lightgrey',
                             num_rows=min(25, len(updatedData)))
                ]
            ]
        group.append([sg.Tab(tab, tabLayout)])

    layout = [[sg.TabGroup(group)], [sg.Button("OK")]]
    win = sg.Window("Details", location=LOCATION)
    win.layout(layout)
    while True:
        ev, values = win.read()
        if ev == "OK" or ev == 'exit':
            win.close()
            home.un_hide()
            return ""


def showDetails(totalData, home):
    tabs = totalData['Library Name'].drop_duplicates().values.tolist()
    header_list = totalData.columns.values.tolist()
    group = list()
    for tab in tabs:
        tabData = totalData[totalData['Library Name'] == tab]
        tabData = tabData.drop('Library Name', axis=1)
        tabData = tabData.values.tolist()
        tabLayout = [[sg.Table(values=tabData, headings=header_list[1:], display_row_numbers=False,
                               justification='left', auto_size_columns=True, background_color='white',
                               alternating_row_color='lightgrey', num_rows=min(25, len(totalData)))]]
        group.append([sg.Tab(tab, tabLayout)])

    layout = [[sg.TabGroup(group)], [sg.Button("OK")]]
    win = sg.Window("Details", location=LOCATION)
    win.layout(layout)
    while True:
        ev, values = win.read()
        if ev == "OK" or ev == 'exit':
            win.close()
            home.un_hide()
            return ""


def selectAllLibraries(ev, home):
    if ev == "selectAllLibs":
        for lib in os.listdir(str(PATH_LIBS)):
            if lib.endswith(".xml"):
                home[lib.replace(".xml", "")].update(True)


def selectAllProducts(ev, home):
    if ev == "selectAllProducts":
        for lib in os.listdir(str(PATH_TEMPLATES)):
            if lib.endswith(".xml"):
                home[lib.replace(".xml", "")].update(True)


def selectAllExcels(ev, home):
    if ev == "selectAllFiles":
        for lib in os.listdir(str(PATH_EXCELS)):
            home[lib].update(True)


def deSelectAllExcels(home):
    for lib in os.listdir(str(PATH_EXCELS)):
        if isExcelFile(lib):
            home[lib].update(False)


def deSelectAllLibraries(home):
    for lib in os.listdir(str(PATH_LIBS)):
        if lib.endswith(".xml"):
            home[lib.replace(".xml", "")].update(False)


def deSelectAllProducts(home):
    for lib in os.listdir(str(PATH_TEMPLATES)):
        if lib.endswith(".xml"):
            home[lib.replace(".xml", "")].update(False)


def getValueOfOptions(selectedOption):
    parts = ""
    if selectedOption != "":
        if selectedOption == 'Risk patterns & Rules':
            parts = ""
        if selectedOption == 'Risk patterns':
            parts = "riskPatterns"
        if selectedOption == 'Rules':
            parts = "rules"
    return parts


def getSelectedLibs(values, files):
    for lib in os.listdir(str(PATH_LIBS)):
        if lib.endswith(".xml"):
            if values[lib.replace(".xml", "")]:
                files.append(PATH_LIBS / lib)
    return files


def getSelectedProducts(values, files):
    for lib in os.listdir(str(PATH_TEMPLATES)):
        if lib.endswith(".xml"):
            if values[lib.replace(".xml", "")]:
                files.append(PATH_TEMPLATES / lib)
    return files


def getSelectedExcels(values, files):
    for file in os.listdir(str(PATH_EXCELS)):
        if isExcelFile(file) and values[file]:
            files.append(PATH_EXCELS / file)
    return files


def getSelectedData(values, files):
    normalChangeLog = False
    if values['fileOldLibraryInput'] != '' and values['fileUpdatedLibraryInput'] != '':
        files.append(values['fileUpdatedLibraryInput'])
        files.append(values['fileOldLibraryInput'])
    else:
        normalChangeLog = True

    return files, normalChangeLog


def showMainFrame(home):
    home["frameUpgrade"].update(visible=False)
    home["frameNewCopy"].update(visible=False)
    home["frameLibs"].update(visible=False)
    home["frameProducts"].update(visible=False)
    home["frameExcels"].update(visible=False)
    home["options"].update(visible=False)
    home["standards"].update(visible=False)
    home["serverConfig"].update(visible=False)
    home["frameResults"].update(visible=False)
    home["mainFrame"].update(visible=True)
    home["buttons"].update(visible=False)
    home["changeLogFrame"].update(visible=False)
    home["standardsFrame"].update(visible=False)
    home["frameQuestion"].update(visible=False)
    home["exit"].update(visible=True)


def getCommandOS():
    command = ""
    if sys.platform == 'darwin':
        command = 'open'
    elif sys.platform == 'linux':
        command = 'nautilus'
    elif sys.platform == 'win32':
        command = 'start'
    return command


def selectionWindow(title, home, showChangeLogOptions=False, showOptions=False, showStandards=False,
                    showServerConfig=False, showExcelOptions=False, showExistingStandards=False, showUpgrade=False,
                    showProductOptions=False, showQuestionOptions=False, showNewCopy=False):
    data = Data()
    data.normalChangeLog = False

    home["frameLibs"].update(visible=True)
    home["mainFrame"].update(visible=False)
    home["existingStandards"].update(visible=False)
    home["buttons"].update(visible=True)
    home["exit"].update(visible=False)
    if showProductOptions:
        home["frameLibs"].update(visible=False)
        home["frameProducts"].update(visible=True)
    if showUpgrade:
        home["frameUpgrade"].update(visible=True)
        home["frameLibs"].update(visible=False)
        home["frameExcels"].update(visible=False)
    if showOptions:
        home["options"].update(visible=True)
    if showStandards:
        home["frameLibs"].update(visible=False)
        home["standardsFrame"].update(visible=True)
    if showServerConfig:
        home["serverConfig"].update(visible=True)
    if showExcelOptions:
        home["frameExcels"].update(visible=True)
        home["frameLibs"].update(visible=False)
        home["frameUpgrade"].update(visible=False)
    if showExistingStandards:
        home["existingStandards"].update(visible=True)
    if showChangeLogOptions:
        home["frameLibs"].update(visible=False)
        home["changeLogFrame"].update(visible=True)
    if showQuestionOptions:
        home["frameQuestion"].update(visible=True)
    if showNewCopy:
        home["frameNewCopy"].update(visible=True)
        home["frameLibs"].update(visible=False)
        home["frameExcels"].update(visible=False)
    startProgressBar(home)

    data.files = list()

    noneCount = 0
    while True:
        ev, values = home.read()

        noneCount += 1
        if noneCount > 10:
            logger.info("Can't read anything from the main window. Finishing...")
            sys.exit()

        selectAllLibraries(ev, home)
        selectAllProducts(ev, home)
        selectAllExcels(ev, home)
        checkConnection(ev, home, values)

        if ev == 'About...':
            sg.popup('About', 'IriusRisk Toolkit UI - Continuum Security', toolkitVersion)

        if ev == "cancel" or ev == 'exit':
            home['fileBrowseValue'].update('')
            home['fileBrowseValueProduct'].update('')
            home['fileBrowseValueExcel'].update('')
            data = Data()
            data.cancel = True
            showMainFrame(home)
            return data

        if ev == 'showFolderOldRelease':
            try:
                os.system('%s %s &' % (getCommandOS(), str(Path.cwd() / "inputFiles" / "oldRelease")))
            except:
                logger.info("The File Browse is not been able to open")

        if ev == 'showFolderUpdatedRelease':
            try:
                os.system('%s %s &' % (getCommandOS(), str(Path.cwd() / "inputFiles" / "updatedRelease")))
            except:
                logger.info("The File Browse is not been able to open")

        if ev == "loadRiskPatterns":
            riskPatterns = set()
            if str(values['browse']) != '':
                root = etree.parse(str(values['browse'])).getroot()
                for riskPattern in root.find("components").iter("component"):
                    riskPatterns.add(riskPattern.attrib['ref'])

                home['comboRiskPatterns'].update(values=sorted(riskPatterns, key=str.lower))

        if ev == "submit":
            progressBar(home)
            home.refresh()
            # input("Press Enter to continue...")
            data.libraryMaster = values['libraryMaster']
            data.libraryNewVersion = values['libraryNewVersion']
            data.parts = getValueOfOptions(values['comboOptions'])
            if showStandards:
                data.files = values['fileLibraryInputStandard']
                data.csv = values['fileCSVInputStandard']
                keys = ['exportStandard', 'addStandard', 'deleteStandard']
                selectedValue = None
                for i in keys:
                    if values[i]:
                        selectedValue = i
                data.parts = selectedValue
            data.files = getSelectedLibs(values, data.files)
            if showExcelOptions:
                data.files = getSelectedExcels(values, data.files)
            if showChangeLogOptions:
                data.files, data.normalChangeLog = getSelectedData(values, data.files)
            if showProductOptions:
                data.files = getSelectedProducts(values, data.files)
            if showExistingStandards:
                data.selectedStandard_path = values['comboExistingStandards']
            if showQuestionOptions:
                data.parts = values['comboQuestions']
                data.value = values['textValueQuestion']
                data.riskPattern = values['comboRiskPatterns']
            if showNewCopy:
                data.parts = values['newCopyLibraryBrowse']
                data.filename = values['newCopyLibraryFileName']
                data.name = values['newCopyLibraryName']
                data.ref = values['newCopyLibraryRef']
                data.userWantsASVS3 = values['checkboxNewCopy']
            if values['fileBrowseValueExcel'] != "":
                data.files.append(Path(values['fileBrowseValueExcel']))
                home['fileBrowseValueExcel'].update('')
            if values['fileBrowseValue'] != "":
                data.files.append(Path(values['fileBrowseValue']))
                home['fileBrowseValue'].update('')
            if values['fileBrowseValueProduct'] != "":
                data.files.append(Path(values['fileBrowseValueProduct']))
                home['fileBrowseValueProduct'].update('')
            if values['apiToken'] != "" and values['urlServer'] != "":
                data.serverUrl = values['urlServer']
                data.apiToken = values['apiToken']
                writeConfig(data.serverUrl, data.apiToken)

            deSelectAllProducts(home)
            deSelectAllLibraries(home)
            deSelectAllExcels(home)
            showMainFrame(home)

            return data


def checkIfConvertXmlToExcel(event, results, home, links):
    if "Convert XML file to Excel file" in event:
        startProgressBar(home)
        libArray = list()
        for lib in os.listdir(str(Path.cwd() / "libraries")):
            if lib.endswith(".xml"):
                libArray.append(lib)
        data = selectionWindow(
            title="Select the library or libraries to generate the Excel file:",
            home=home)

        for file in data.files:
            if file.name.endswith(".xml"):
                excelPath = Path.cwd() / "outFiles" / "spreadSheets" / str(file.name.replace(".xml", ".xlsx"))
                link = convertXmlToExcel(
                    xmlPath=file,
                    excelPath=excelPath)
                results += "Library '%s' was converted to Excel file successfully and the output file is in the path '%s'.\n" % (
                    str(file.name), Path.cwd() / "outFiles" / "spreadSheets" / file.name.replace(".xml", ".xlsx"))
                links.append(link)
            else:
                results += "File '%s' is not converted, because its extension is wrong" % file

    return results, links


def checkIfConvertExcelToXml(event, results, home, links):
    if "Convert Excel file to XML file" in event:
        data = selectionWindow(
            title="Select the library or libraries to generate the XML file:",
            showExcelOptions=True,
            home=home)
        for file in data.files:
            if isExcelFile(file.name):
                results += convertExcelToXml(excelFilePath=Path.cwd() / "inputFiles" / "spreadSheetFiles" / file)
                links.append(Path.cwd() / "outFiles" / "outputLibs" / file.name.replace(".xlsx", ".xml"))
            else:
                results += "File '%s' is not converted, because its extension is wrong" % file

    return results, links


def checkIfConvertXmlToHtml(event, results, home, links):
    if "Generate HTML file from XML file" in event:
        libArray = list()
        for lib in os.listdir(str(Path.cwd() / "libraries")):
            if lib.endswith(".xml"):
                libArray.append(lib)
        data = selectionWindow(
            title="Select the library or libraries to generate the HTML file:",
            home=home)

        for file in data.files:
            if file.name.endswith(".xml"):
                generateHTML(
                    xml_path=Path.cwd() / "libraries" / file,
                    html_path=Path.cwd() / "outFiles" / "generatedHtml" / file.name.replace(".xml", ".html"))
                results += "Library '%s' was converted to HTML file successfully and the output file is in the path '%s'.\n" % (
                    file.name.replace(".xml", ""),
                    Path.cwd() / "outFiles" / "generatedHtml" / file.name.replace(".xml", ".html"))
                links.append(Path.cwd() / "outFiles" / "generatedHtml" / file.name.replace(".xml", ".html"))
            else:
                results += "File HTML '%s' is not generated, because its extension is wrong" % file
    return results, links


def checkIfLibraryDetails(event, results, home, links):
    if "Show library details" in event:
        libs_path = Path.cwd() / "libraries"
        libs = list()
        for lib in os.listdir(str(libs_path)):
            if lib.endswith(".xml"):
                libs.append(lib)
        data = selectionWindow(
            title="Select the library or libraries to show the library details:",
            home=home)

        columns = ['Library Name', 'Risk Pattern', '# Use Cases', '# Threats', '# Weaknesses', '# Countermeasures']
        totalData = pd.DataFrame([], columns=columns)
        for file in data.files:
            if file.name.endswith(".xml"):
                data = readInfoFromXml(libs_path / file, columns)
                totalData = totalData.append(data)
                results += "The details of the library '%s' are shown in other window.\n" % file.name.replace(".xml",
                                                                                                              "")
            else:
                results += "Details from file '%s' are not shown, because its extension is wrong.\n" % file.name.replace(
                    ".xml", "")
        if not totalData.empty:
            showDetails(totalData, home)

    return results, links


def checkIfChangeLog(event, results, home, links):
    if "Generate the ChangeLog file from two versions" in event:
        data = selectionWindow(
            title="Select the library or libraries to generate the XML file:",
            showChangeLogOptions=True,
            home=home)
        if not data.cancel:
            if data.normalChangeLog:
                results, outFiles = generateChangeLog([])
                links.append(outFiles)
            if not data.normalChangeLog:
                results, outFiles = generateChangeLog(data.files)
                links.append(outFiles)

    return results, links


def checkIfAddStandardToLibrary(event, results, home, links):
    # select library with options (standard from a list)
    if "Add Standard to library or libraries" in event:
        data = selectionWindow(
            title="Select the library or libraries to add the selected standard:",
            showStandards=True,
            home=home)

        # Library path
        file = data.files

        # Radio option
        option = data.parts

        results = ""
        standard_path_csv = Path.cwd() / "inputFiles" / "standardsFiles" / "standardEditor.csv"

        if hasattr(data, "csv"):
            if data.csv != "":
                standard_path_csv = data.csv

        links = []

        if file:
            if file.endswith(".xml"):

                filePath = Path(file)
                fileOut = Path.cwd() / "outFiles" / "outputLibs" / str(filePath.name)

                if option == "exportStandard":
                    getStandards(file, standard_path_csv)
                    results += f"Standards from library {file} exported to CSV without problem: {standard_path_csv}"
                elif option == "addStandard":
                    setStandard(standard_path_csv, file, fileOut, "add")
                    results += f"Added standards from {file} to {fileOut} from {standard_path_csv}"
                elif option == "deleteStandard":
                    setStandard(standard_path_csv, file, fileOut, "delete")
                    results += f"Removed standards from {file} to {fileOut} from {standard_path_csv}"
                else:
                    results += "No valid option found. Please select one of the displayed options."
            else:
                results += f"Can't process file '{file}', because its extension is wrong"

    return results, links


def checkIfUpgradeLibraryFromOtherFile(event, results, home, links):
    path_new_library = Path.cwd() / "inputFiles" / "libsToMerge"
    if "Upgrade a library with other version of the same library" in event:
        path_library = Path.cwd() / "libraries"
        libArray = list()
        for lib in os.listdir(str(path_library)):
            if lib.endswith(".xml"):
                libArray.append(lib)
        data = selectionWindow("Select the main library and the secondary library to upgrade it:", showUpgrade=True,
                               home=home)

        if str(data.libraryMaster) != "" and str(data.libraryNewVersion) != "":
            results = mergeLibrariesByPaths(path_library / str(data.libraryMaster + ".xml"),
                                            path_new_library / str(data.libraryNewVersion + ".xml"))
            links.append(path_new_library / str(data.libraryNewVersion + ".xml"))
    return results, links


def checkIfGenerateHtmlFileWithStandardsVsCountermeasures(event, results, home, links):
    if "Generate HTML file with the relationships between a standard and the countermeasures" in event:

        data = selectionWindow(
            "Select the standard to generate the HTML file:",
            showExistingStandards=True,
            home=home)

        if data.selectedStandard_path != "":
            path = Path.cwd() / "inputFiles" / "descriptionOfStandards"
            results, output_path = generateHtmlFromLibrariesAndStandard(
                path / str("standard_" + data.selectedStandard_path + "_info.csv"), data.files)
            links.append(output_path)
    return results, links


def checkIfUploadLibrariesToServer(event, results, home, links):
    if "Upload the selected libraries to the configured server" in event:
        data = selectionWindow(
            title="Select the library or libraries to test the threat mitigation:",
            showServerConfig=True,
            home=home)
        for file in data.files:
            removeLibraryByApi(PATH_LIBS / file, data.serverUrl, data.apiToken)

        for file in data.files:
            results += uploadLibraryByApi(PATH_LIBS / file, data.serverUrl, data.apiToken)

    return results, links


def checkIfAddReferencesFromExcel(event, results, home, links):
    files = []
    excels_path = Path.cwd() / "inputFiles" / "externalSpreadsheets"
    if "Add control references using the mapping from Excel file" in event:
        files += [each for each in os.listdir(str(excels_path)) if isExcelFile(each)]
        excelFile, replaceLibs = selectionOfExcelFile(
            "Generate the libraries with the new references in the countermeasures", files, excels_path, home)

        if excelFile != "":
            results += addReferencesToLibrariesByExcelFile(excels_path / excelFile, replaceLibs, excelFile)

    return results, links


def checkIfConvertRulesFromExcelToXML(event, results, home, links):
    files = []
    excels_path = Path.cwd() / "inputFiles" / "externalSpreadsheets" / "rulesEditor"
    if "Convert Rules from Excel file to XML file" in event:
        files += [each for each in os.listdir(str(excels_path)) if isExcelFile(each)]
        excelFile = selectionOfExcelRulesFile("Select the Rules Editor Excel utility file", files, excels_path, home)

        if excelFile != "":
            results += convertRulesFromExcelToXML(excels_path / excelFile)
            links.append(Path.cwd() / "outFiles" / "rulesEditorLibraries" / excelFile.replace(".xlsx", ".xml"))

    return results, links


def checkIfRiskFromXML(event, results, home, links):
    if "Show risk calculation from XML product file" in event:
        startProgressBar(home)

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


def checkIfGenerateRulesAnswers(event, results, home, links):
    if "Questions about rules" in event:
        startProgressBar(home)
        data = selectionWindow(
            title="Select the library or libraries:",
            showQuestionOptions=True,
            home=home)

        # Check if the question applies to all marked libraries separately
        if data.parts in questions.values():
            check = True
            if data.parts in [questions[1], questions[2]]:
                check = False
            searchValue = ""
            if hasattr(data, "value"):
                searchValue = data.value
            if hasattr(data, "riskPattern") and data.riskPattern != "":
                searchValue = data.riskPattern
            links = generateRulesHtml(data.files, question=data.parts, checkAllRules=check, value=searchValue)
            results += f"Rules that answer the question '{data.parts}' successfully retrieved and the output file/s is/are in the path/s {links}.\n"

    return results, links


def checkIfCreateLibraryFromDefaultOne(event, results, home, links):
    if "Create a new library from a default one" in event:
        path_new_library = Path.cwd() / "outFiles" / "libraries"

        data = selectionWindow("Select the main library and the secondary library to upgrade it:", showNewCopy=True,
                               home=home)

        if not data.cancel:
            missing = []
            if str(data.parts) == "":
                missing.append("base library")
            if str(data.filename) == "":
                missing.append("filename")
            if str(data.name) == "":
                missing.append("name")
            if str(data.ref) == "":
                missing.append("ref")

            if not missing:
                try:
                    newCopy = createLibraryFromDefaultOne(baseLibrary=Path(data.parts),
                                                          outPath=path_new_library / str(data.filename),
                                                          name=data.name,
                                                          ref=data.ref,
                                                          userWantsASVS3=data.userWantsASVS3)
                    results = "Copy successful. The new library has been generated in " + str(newCopy)
                except:
                    results = "An error occurred when creating the new library. Try again"
            else:
                results = f"Some required fields have not been found: {', '.join(missing)} . Please try it again"

    return results, links


def checkIfRunTestsForLibraries(event, results, home, links):
    if "Run tests for libraries" in event:
        root = Tk()

        view = MainWindow(root)
        view.project = view.load_project(root, UnittestProject)
        view.mainloop()

        # After closing the window...
        root.destroy()

    return results, links


def loadMainLayout():

    layout = []
    for i in range(0, len(options)):
        layout.append([sg.Button(f"{i+1}. {options[i]}", button_color=BUTTON_COLOR, size=SIZE_ELEMENT)])

    return layout


def main():
    print('starting up...')  # Seems to help repl.it
    logger.info("App UI launched")
    sg.SetOptions(element_padding=(10, 3), auto_size_buttons=True, margins=(4, 4), text_justification='Left',
                  background_color='#e1e1e1', element_background_color='#e1e1e1',
                  text_element_background_color='#e1e1e1',
                  icon=str(Path.cwd() / "inputFiles" / "IriusRiskToolKitUI_icon.ICO"))

    layout = loadMainLayout()
    layoutLibs = getLayoutLibs()
    layoutProducts = getLayoutProducts()
    layoutExcels = getLayoutExcels()
    layoutUpgrade = getLayoutUpgrade()
    layoutNewCopy = getLayoutNewCopy()
    changeLogLayout = getChangeLogLayout()
    standardsLayout = getStandardsLayout()
    layoutResults = [[]]

    menu_def = [['Help', 'About...'], ]

    mainLayout = [[
        sg.Menu(menu_def),
        sg.Frame("Select the action to do:", layout, key='mainFrame'),
        sg.Frame("Select the libraries to use:", layoutLibs, key='frameLibs', visible=False),
        sg.Frame("Select the products to use:", layoutProducts, key='frameProducts', visible=False),
        sg.Frame("Select the Excels to use:", layoutExcels, key='frameExcels', visible=False),
        sg.Frame("Upgrading library:", layoutUpgrade, key='frameUpgrade', visible=False),
        sg.Frame("Create a new library from a default one:", layoutNewCopy, key='frameNewCopy', visible=False),
        sg.Frame("Select libraries to generate the ChangeLog:", changeLogLayout, key='changeLogFrame', visible=False),
        sg.Frame("Select a library to add/delete standards:", standardsLayout, key='standardsFrame', visible=False),
        sg.Frame("Results:", layoutResults, key='frameResults', visible=False)],
        [sg.Frame("", [[sg.Text("Ready!", size=SIZE_ELEMENT, key='progbar', text_color='white',
                                background_color='royal blue', justification='center')]], key='status', visible=True)],
        [sg.Frame("", [[sg.Button("Submit", key='submit'), sg.Button("Cancel", key='cancel')]], key='buttons',
                  visible=False)], [sg.Button('Exit', key='exit')]
    ]
    home = sg.Window('IriusRiskToolKitUI', mainLayout, location=LOCATION, auto_size_text=True)

    while True:
        results = ""
        event, vals1 = home.read()
        if event is not None and event != "":
            logger.info("Event '%s' is selected." % event)
        if event == 'About...':
            sg.popup('About', 'IriusRisk Toolkit UI - Continuum Security', toolkitVersion)
        if (event == "exit") or (event == sg.WIN_CLOSED):
            break
        showMainFrame(home)
        links = list()
        results, links = checkIfConvertXmlToExcel(event, results, home, links)
        results, links = checkIfConvertExcelToXml(event, results, home, links)
        results, links = checkIfConvertXmlToHtml(event, results, home, links)
        results, links = checkIfLibraryDetails(event, results, home, links)
        results, links = checkIfChangeLog(event, results, home, links)
        results, links = checkIfAddStandardToLibrary(event, results, home, links)
        results, links = checkIfUpgradeLibraryFromOtherFile(event, results, home, links)
        results, links = checkIfGenerateHtmlFileWithStandardsVsCountermeasures(event, results, home, links)
        results, links = checkIfUploadLibrariesToServer(event, results, home, links)
        results, links = checkIfAddReferencesFromExcel(event, results, home, links)
        results, links = checkIfConvertRulesFromExcelToXML(event, results, home, links)
        results, links = checkIfRiskFromXML(event, results, home, links)
        results, links = checkIfGenerateRulesAnswers(event, results, home, links)
        results, links = checkIfCreateLibraryFromDefaultOne(event, results, home, links)
        results, links = checkIfRunTestsForLibraries(event, results, home, links)

        finishProgressBar(home)
        logger.info("Results page is shown.")
        showLinks(links, results, home)
        startProgressBar(home)

    home.close()


if __name__ == '__main__':
    main()
