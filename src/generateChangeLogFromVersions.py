from pathlib import Path
import os
from lxml import etree
import logging
from src.common import isXmlFile
from src.generateChangeLogFromVersionsList import createCardBodyModifiedList, compareLibs
from html import escape
import pandas as pd
import re
# Create and configure logger
# filemode = 'w' that will change the mode of operation from "append" to "write" and will overwrite the file every time we run our application
logging.basicConfig(filename="logFile.log",
                    format='%(asctime)s  %(levelname)-10s %(message)s',
                    datefmt="%Y-%m-%d-%H-%M-%S",
                    filemode='w')

# Creating an object
logger = logging.getLogger()

# Setting the threshold of logger to INFO
logger.setLevel(logging.INFO)
parser = etree.HTMLParser(encoding='utf-8')
green = 'style="color:green"'
red = 'style="color:red"'
yellow = 'style="color:darkgoldenrod"'

blank = re.compile('[\n ]+')
asciiMatcher = re.compile('[\x00-\x7F]')
names = {
    "project": "Project",
    "desc": "Description",
    "categoryComponents": "Category Components",
    "categoryComponent": "Category Component",
    "riskPatterns": "Risk Patterns",
    "riskPattern": "Risk Pattern",
    "componentDefinitions": "Component Definitions",
    "componentDefinition": "Component Definition",
    "supportedStandards": "Supported Standards",
    "supportedStandard": "Supported Standard"
}
num = 1


def normalization(word):
    if word in names.keys():
        return names[word]
    else:
        return word.capitalize()


def generateHtmlForChangeLog(libraries, outFile_path):
    base_html_path = Path.cwd() / "src" / "resources" / "changelog_base_html.html"
    file = etree.parse(str(base_html_path), parser)
    root = file.getroot()

    head = root.find("head")
    style = etree.Element("style")
    style.text = "li:hover.ir-collapsible { background-color: #c3eaf9 } "
    head.append(style)

    body = root.find("body")

    accordion = createTitleHtmlFile(title="Change log", body=body)

    createCardsForAllLibraries(libraries, accordion, body)

    data = etree.tostring(root, pretty_print=True, method="html", encoding='utf-8')
    fileOutput = open(str(outFile_path), 'wb')
    fileOutput.write(data)
    fileOutput.close()


def createTitleHtmlFile(title, body):
    h1Element = etree.Element("h1")
    h1Element.text = title
    h1Element.set("style", "justify-content: center;text-align: center;font-weight: bold;")

    body.append(h1Element)
    accordion = etree.Element("div")
    accordion.set("id", "accordion")

    return accordion


def createCardsForAllLibraries(libraries, accordion, body):
    numH = 0
    for library, data, dataFrame in libraries:
        if isXmlFile(library):
            numH = numH+1
            card = createCardHeader(library, numH, data)
            if data not in ["NEW", "OTHER"]:
                card = createCardBodyModified(card, numH, data)
                card = createCardBodyModifiedList(card, numH, dataFrame, library)

            accordion.append(card)

            body.append(accordion)
    return body


def createCardHeader(library, numH, data):
    card = etree.Element("div")
    cardheader = etree.Element("div")
    cardheader.set('id', 'heading' + str(numH))
    h5 = etree.Element("h5")
    h5.set("class", "mb-0")

    button = etree.Element("button")

    button.set('data-toggle', 'collapse')
    button.set('data-target', '#collapseH' + str(numH) + ',#collapseL' + str(numH))
    button.set('aria-expanded', 'false')
    button.set('aria-controls', 'collapseH' + str(numH) + ',#collapseL' + str(numH))

    if data == "NEW":
        card.set("class", "card border-success")
        cardheader.set("class", "card-header text-white bg-success")
        button.set('class', 'btn btn-success btn-group-toggle text-white ')
    elif data == "":
        card.set("class", "card border-light")
        cardheader.set("class", "card-header")
        button.set('class', 'btn btn-light')
    else:
        card.set("class", "card border-warning")
        cardheader.set("class", "card-header text-white bg-warning")
        button.set('class', 'btn btn-warning btn-group-toggle text-white ')

    h5.append(button)
    cardheader.append(h5)
    button.text = "Library: %s" % library
    card.append(cardheader)
    return card


def createCardBodyModified(card, numH, data):
    carddivbody = etree.Element("div")
    carddivbody.set('id', 'collapseH' + str(numH))
    carddivbody.set('class', 'collapse')
    carddivbody.set('aria-labelledby', 'heading' + str(numH))
    carddivbody.set('data-parent', '#accordion')

    carddivbody.append(data)

    card.append(carddivbody)
    return card


def attributeChanges(updatedNode, oldNode):
    string = ""
    for attribute in updatedNode.attrib:
        if attribute not in oldNode.attrib:
            string += f"<li {green}>Added attribute: <b>{attribute}</b></li>"
        else:
            if updatedNode.attrib[attribute] != oldNode.attrib[attribute]:
                string += f"<li>Modified attribute {attribute}: <span {yellow}>{oldNode.attrib[attribute]}</span> -> <span {green}><b>{updatedNode.attrib[attribute]}</b></span></li>"
    for attribute in oldNode.attrib:
        if attribute not in updatedNode.attrib:
            string += f"<li {red}>Deleted attribute: <b>{attribute}</b></li>"

    if not blank.match(str(updatedNode.text)):
        if updatedNode.text != oldNode.text and asciiMatcher.match(str(oldNode.text)) and asciiMatcher.match(str(updatedNode.text)) \
                and oldNode.text and updatedNode.text:
            string += f"<li>Modified {updatedNode.tag}: <span {yellow}>{escape(oldNode.text)}</span> -> <span {green}><b>{escape(updatedNode.text)}</b></span></li>"
        elif updatedNode.text is None and oldNode.text is not None:
            string += f"<li>Modified {updatedNode.tag}: <span {yellow}>{escape(oldNode.text)}</span> -> <span {green}><b>None</b></span></li>"
        elif oldNode.text is None and updatedNode.text is not None:
            string += f"<li>Modified {updatedNode.tag}: <span {yellow}>None</span> -> <span {green}><b>{escape(updatedNode.text)}</b></span></li>"
        elif updatedNode.text != oldNode.text:
            string += f"<li>Modified {updatedNode.tag}: Please check the original source as there are non-ASCII characters in this text</li>"

    return string


def compareRuleConditionsAndActions(child, orule):
    string = ""
    conditions = [(x.attrib['name'], x.attrib['value']) for x in child if x.tag == 'condition']
    actions = [(x.attrib['name'], x.attrib['value']) for x in child if x.tag == 'action']

    oconditions = [(x.attrib['name'], x.attrib['value']) for x in orule if x.tag == 'condition']
    oactions = [(x.attrib['name'], x.attrib['value']) for x in orule if x.tag == 'action']

    # if the tuple is not in the old conditions its because it is new
    for cond in conditions:
        if cond not in oconditions:
            string += f"<li {green}>New condition on rule {child.attrib['name']}: <b>{str(cond)}</b></li>"

    # if the tuple is not in the new conditions its because it is deleted
    for ocond in oconditions:
        if ocond not in conditions:
            string += f"<li {red}>Deleted condition on rule {child.attrib['name']}: <b>{str(ocond)}</b></li>"

    # if the tuple is not in the old actions its because it is new
    for act in actions:
        if act not in oactions:
            string += f"<li {green}>New action on rule {child.attrib['name']}: <b>{str(act)}</b></li>"

    # if the tuple is not in the new actions its because it is deleted
    for oact in oactions:
        if oact not in actions:
            string += f"<li {red}>Deleted action on rule {child.attrib['name']}: <b>{str(oact)}</b></li>"

    return string


def compareStandards(child, ochild):
    # If we are comparing standards we need to check two attributes at the same time
    string = "<ul><li><b>Standards</b></li><ul>"

    childStandards = [(x.attrib['ref'], x.attrib['supportedStandardRef']) for x in child]
    ochildStandards = [(x.attrib['ref'], x.attrib['supportedStandardRef']) for x in ochild]

    for x in childStandards:
        if x not in ochildStandards:
            string += f"<li {green}>Added standard: <b>{str(x)}</b></li>"

    for x in ochildStandards:
        if x not in childStandards:
            string += f"<li {red}>Deleted standard: <b>{str(x)}</b></li>"

    string += "</ul></ul>"

    if "<ul></ul>" in string:
        string = ""

    return string


def compareImplementations(child, ochild):
    # If we are comparing standards we need to check two attributes at the same time
    string = "<ul><li><b>Implementations</b></li><ul>"

    childStandards = [x.attrib['platform'] for x in child]
    ochildStandards = [x.attrib['platform'] for x in ochild]

    for x in childStandards:
        if x not in ochildStandards:
            string += f"<li {green}>Added implementation: <b>{str(x)}</b></li>"

    for x in ochildStandards:
        if x not in childStandards:
            string += f"<li {red}>Deleted implementation: <b>{str(x)}</b></li>"

    string += "</ul></ul>"

    if "<ul></ul>" in string:
        string = ""

    return string


def compareReferences(child, ochild):
    # If we are comparing references we need to check two attributes at the same time
    string = "<ul><li><b>References</b></li><ul>"

    childReferences = [(x.attrib['name'], x.attrib['url']) for x in child]
    ochildReferences = [(x.attrib['name'], x.attrib['url']) for x in ochild]

    for x in childReferences:
        if x not in ochildReferences:
            string += f"<li {green}>Added reference: <b>{str(x)}</b></li>"

    for x in ochildReferences:
        if x not in childReferences:
            string += f"<li {red}>Deleted reference: <b>{str(x)}</b></li>"

    string += "</ul></ul>"

    if "<ul></ul>" in string:
        string = ""

    return string


def recCompare(unode, onode):
    global num
    # First we compare the node attributes to see if any has changed
    ul = etree.Element("ul")
    li = etree.Element("li")
    li.set('data-toggle', 'collapse')
    li.set('data-target', '#collapse'+str(num))
    li.set('aria-expanded', 'false')
    li.set('aria-controls', 'collapse'+str(num))
    li.set('class', 'ir-collapsible font-weight-bold')
    ul2 = etree.Element("ul")
    ul2.set('id', 'collapse'+str(num))
    ul2.set('class', 'collapse')

    num += 1

    if "ref" in unode.attrib:
        li.text = f"{normalization(unode.tag)}: "
        b = etree.Element("b")
        b.text = unode.attrib['ref']
        li.append(b)
    else:
        li.text = f"{normalization(unode.tag)}"
    ul.append(li)

    string = attributeChanges(unode, onode)
    if string != "":
        ul2.append(etree.fromstring(string, parser=parser))

    # Second we check what child nodes have been added or deleted by checking the node tags
    childListTags = [x.tag for x in unode]
    ochildListTags = [x.tag for x in onode]

    # Added (nodes in the new list that aren't in the old list)
    for tag in childListTags:
        if tag not in ochildListTags:
            string += f"<li {green}>Added tag: <b>{tag}</b></li>"
            ul2.append(etree.fromstring(string, parser=parser))

    # Deleted (nodes in the old list that aren't in the new list)
    for tag in ochildListTags:
        if tag not in childListTags:
            string = f"<li {red}>Deleted tag: <b>{tag}</b></li>"
            ul2.append(etree.fromstring(string, parser=parser))

    # Third we check every child
    childList = [x for x in unode]
    ochildList = [x for x in onode]

    # Here we check removed nodes from child list with same tag
    ochilddList = [x for x in ochildList if "ref" in x.attrib]
    childRefsList = [x.attrib['ref'] for x in childList if "ref" in x.attrib]
    for ochild in ochilddList:
        if ochild.attrib['ref'] not in childRefsList:
            string = f"<li {red}>Deleted {ochild.tag} : <b>{ochild.attrib['ref']}</b>"
            if ochild.tag in ["component", "usecase"]:
                if len(list(ochild.iter("threat"))) != 0:
                    string += " [ "
                    for th in ochild.iter("threat"):
                        string += th.attrib['ref'] + ", "
                    string = string[:-2] + " ]</li>"
            else:
                string += "</li>"
            ul2.append(etree.fromstring(string, parser=parser))

    # Here we apply specific behaviour if the node tag is "rules" because it is a bit complicated
    if unode.tag == "rules":
        ochilddList = [x for x in ochildList if "name" in x.attrib]
        childRefsList = [x.attrib['name'] for x in childList if "name" in x.attrib]
        for ochild in ochilddList:
            if ochild.attrib['name'] not in childRefsList:
                string = f"<li {red}>Deleted {ochild.tag} : <b>{ochild.attrib['name']}</b></li>"
                ul2.append(etree.fromstring(string, parser=parser))

    # For every child in the node...
    for child in childList:
        # Same as before, if the tag is "rule" we apply specific behaviour
        if child.tag == "rule":
            ochildRefsList = [x.attrib['name'] for x in ochildList if "name" in x.attrib]
            if child.attrib['name'] not in ochildRefsList:
                string = f"<li {green}>Added new {child.tag} : <b>{child.attrib['name']}</b></li>"
                ul2.append(etree.fromstring(string, parser=parser))

            for orule in ochildList:
                if child.attrib['name'] == orule.attrib['name']:
                    string = attributeChanges(child, orule)
                    string += compareRuleConditionsAndActions(child, orule)
                    if string != "":
                        ul2.append(etree.fromstring(string, parser=parser))

        elif child.tag == "standards":
            ochildStandardList = [x for x in ochildList if x.tag == "standards"]
            string = ""
            if ochildStandardList:
                ochildSt = ochildStandardList[0]
                string = compareStandards(child, ochildSt)
            if string != "":
                ul2.append(etree.fromstring(string, parser=parser))

        elif child.tag == "implementations":
            ochildImplementationsList = [x for x in ochildList if x.tag == "implementations"]
            string = ""
            if ochildImplementationsList:
                ochildImp = ochildImplementationsList[0]
                string = compareImplementations(child, ochildImp)
            if string != "":
                ul2.append(etree.fromstring(string, parser=parser))

        elif child.tag == "references":
            ochildReferenceList = [x for x in ochildList if x.tag == "references"]
            string = ""
            if ochildReferenceList:
                ochildRef = ochildReferenceList[0]
                string = compareReferences(child, ochildRef)
            if string != "":
                ul2.append(etree.fromstring(string, parser=parser))

        else:
            # In other case we check that if the child has attribute "ref" we need to take that into account
            if "ref" in child.attrib:
                # Need to see if the child is new or modified
                # New
                ochildRefsList = [x.attrib['ref'] for x in ochildList if "ref" in x.attrib]
                if child.attrib['ref'] not in ochildRefsList:
                    string = f"<li {green}>Added new {child.tag} : <b>{child.attrib['ref']}</b>"

                    # We add to the message the new threats
                    if child.tag in ["component", "usecase"]:
                        if len(list(child.iter("threat"))) != 0:
                            string += " [ "
                            for th in child.iter("threat"):
                                string += th.attrib['ref']+", "
                            string = string[:-2] + " ]</li>"
                    else:
                        string += "</li>"
                    ul2.append(etree.fromstring(string, parser=parser))

            # Comparing the old nodes with the new ones we call this function again with the child nodes
            for ochild in ochildList:
                if child.tag == ochild.tag:
                    if "ref" not in ochild.attrib:
                        elem = recCompare(child, ochild)

                        for e in elem:
                            if e.tag == "ul":
                                if len(e) != 0:
                                    ul2.append(elem)
                        break
                    if "ref" in ochild.attrib and child.attrib['ref'] == ochild.attrib['ref']:
                        elem = recCompare(child, ochild)

                        for e in elem:
                            if e.tag == "ul":
                                if len(e) != 0:
                                    ul2.append(elem)
                        break

    ul.append(ul2)

    return ul


def compareLibraries(updatedLibrary, oldLibrary, outFile_path):
    updatedLibName = Path(updatedLibrary).name

    updatedRoot = etree.parse(str(updatedLibrary)).getroot()
    oldRoot = etree.parse(str(oldLibrary)).getroot()

    data = recCompare(updatedRoot, oldRoot)

    ### To get list of changes
    array = list()
    array = compareLibs(updatedLibrary, oldLibrary, updatedLibName, array)

    dfm = pd.DataFrame(array, columns=['Library', 'Data type', 'Action', 'Name', 'Reason'])
    logger.info("DataFrame was generated with the data of the libraries")

    if len(dfm.loc[dfm['Library'] == updatedLibName, ['Library']]) > 1:
        array.append([updatedLibName, 'Library', "Edited", "", ""])
    dfm = pd.DataFrame(array, columns=['Library', 'Data type', 'Action', 'Name', 'Reason'])
    dataFrame = dfm.sort_values(['Library', 'Data type', 'Action', 'Name'], ascending=[1, 1, 1, 1])

    if data.find("ul").getchildren():
        generateHtmlForChangeLog([(updatedLibName, data, dataFrame)], outFile_path)
        text = "Updated library " + updatedLibrary
    else:
        generateHtmlForChangeLog([], outFile_path)
        text = "No changes in library" + updatedLibrary

    return text


def compareListOfLibraries(folderUpdatedRelease, folderOldRelease, outFile_path):
    updatedLibs = os.listdir(str(folderUpdatedRelease))
    oldLibs = os.listdir(str(folderOldRelease))
    text = ""
    libraries = list()
    for updatedLib in updatedLibs:
        if isXmlFile(updatedLib):
            if updatedLib in oldLibs:
                updatedRoot = etree.parse(str(folderUpdatedRelease / updatedLib)).getroot()
                oldRoot = etree.parse(str(folderOldRelease / oldLibs[oldLibs.index(updatedLib)])).getroot()
                data = recCompare(updatedRoot, oldRoot)

                ### To get list of changes
                array = list()
                array = compareLibs(str(folderUpdatedRelease / updatedLib), str(folderOldRelease / oldLibs[oldLibs.index(updatedLib)]), updatedLib, array)

                dfm = pd.DataFrame(array, columns=['Library', 'Data type', 'Action', 'Name', 'Reason'])
                logger.info("DataFrame was generated with the data of the libraries")

                if len(dfm.loc[dfm['Library'] == updatedLib, ['Library']]) > 1:
                    array.append([updatedLib, 'Library', "Edited", "", ""])
                dfm = pd.DataFrame(array, columns=['Library', 'Data type', 'Action', 'Name', 'Reason'])
                dataFrame = dfm.sort_values(['Library', 'Data type', 'Action', 'Name'], ascending=[1, 1, 1, 1])



                # If there is any change (any "ul" subnodes)
                if data.find("ul").getchildren():
                    text += f"Library {updatedLib} has been updated\n"
                    libraries.append((updatedLib, data, dataFrame))
            else:
                text += f"Library {updatedLib} is new\n"
                libraries.append((updatedLib, "NEW", None))

    generateHtmlForChangeLog(libraries, outFile_path)
    logger.info("HTML file of the Changelog was generated in the path: %s" % outFile_path)

    return text


def generateChangeLog(files):
    outFile_path = Path.cwd() / "outFiles" / "changeLog.html"

    if not files:
        folderUpdatedRelease = Path.cwd() / "inputFiles" / "updatedRelease"
        folderOldRelease = Path.cwd() / "inputFiles" / "oldRelease"
        text = compareListOfLibraries(folderUpdatedRelease, folderOldRelease, outFile_path)
    else:
        updatedLibrary = files[0]
        oldLibrary = files[1]
        text = compareLibraries(updatedLibrary, oldLibrary, outFile_path)

    text += f"--> Changelog file generated in the path: {str(outFile_path)}"
    return text, outFile_path


if __name__ == "__main__":
    fileArray = ["C:\\CS\\Workspace\\iriusrisktoolkitui\\libraries\\3.4.0.xml", "C:\\CS\\Workspace\\iriusrisktoolkitui\\libraries\\3.0.0.xml"]
    fileArray = []
    result, outfile = generateChangeLog(fileArray)
