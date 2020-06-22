import os
import sys
from lxml import etree
from pathlib import Path
from src.common import createTitleHtmlFile, writeToHtml
import logging
import re

home = os.getcwd()
logging.basicConfig(filename="logFile.log",
                    format='%(asctime)s  %(levelname)-10s %(message)s',
                    datefmt="%Y-%m-%d-%H-%M-%S",
                    filemode='w')

# Creating an object
logger = logging.getLogger()

# Setting the threshold of logger to INFO
logger.setLevel(logging.INFO)

questions = {
    0: "Show all rules",
    1: "Show all rules by library",
    2: "For every library which rules use a specific answer?",
    3: "From all the rules which ones import a risk pattern?",
    4: "From all the rules which ones check if a risk pattern exists?",
    5: "What possible ways we have available for a specific risk pattern to appear in the model?"
}


def createCardBodyCondition(condition, card, parent, num):
    root = '#%s' % parent
    carddivbody = etree.Element("div")
    carddivbody.set('id', 'collapse' + str(num))
    carddivbody.set('class', 'collapse')
    carddivbody.set('aria-labelledby', 'heading' + str(num))
    carddivbody.set('data-parent', root)

    cardbody = etree.Element("div")
    cardbody.set("class", "card-body")

    parser = etree.HTMLParser()
    b = etree.Element("b")
    b.append(etree.fromstring("Attributes:", parser))
    cardbody.append(b)
    for name, value in condition.attrib.items():
        cardbody.append(etree.fromstring(f'{name}="{value}"', parser))

    carddivbody.append(cardbody)
    card.append(carddivbody)
    return card


def createCardBodyAction(action, card, parent, num):
    root = '#%s' % parent
    carddivbody = etree.Element("div")
    carddivbody.set('id', 'collapse' + str(num))
    carddivbody.set('class', 'collapse')
    carddivbody.set('aria-labelledby', 'heading' + str(num))
    carddivbody.set('data-parent', root)

    cardbody = etree.Element("div")
    cardbody.set("class", "card-body")

    parser = etree.HTMLParser()
    b = etree.Element("b")
    b.append(etree.fromstring("Attributes:", parser))
    cardbody.append(b)
    for name, value in action.attrib.items():
        cardbody.append(etree.fromstring(f'{name}="{value}"', parser))

    carddivbody.append(cardbody)
    card.append(carddivbody)
    return card


def createCardHeaderConditionAction(title, num):
    card = etree.Element("div")
    cardheader = etree.Element("div")
    cardheader.set('id', 'heading' + str(num))
    h5 = etree.Element("h5")
    h5.set("class", "mb-0")

    button = etree.Element("button")

    button.set('data-toggle', 'collapse')
    button.set('data-target', '#collapse' + str(num))
    button.set('aria-expanded', 'false')
    button.set('aria-controls', 'collapse' + str(num))

    card.set("class", "card border-success")
    cardheader.set("class", "card-header")
    button.set('class', 'btn btn-light btn-group-toggle')

    h5.append(button)
    cardheader.append(h5)
    button.text = title
    card.append(cardheader)
    return card


def createCardConditions(conditions, cardBody, num):
    parent = "parent%i" % num
    parentCard = etree.Element("div")
    parentCard.set("class", "accordion")
    parentCard.set("id", parent)
    for condition in conditions:
        num = num + 1
        name = condition.attrib['name']
        value = condition.attrib['value']
        title = f"Condition: {name} [{value}]"
        card = createCardHeaderConditionAction(title, num)
        card = createCardBodyCondition(condition, card, parent, num)
        parentCard.append(card)
    cardBody.append(parentCard)
    return cardBody, num


def createCardActions(actions, cardBody, num):
    parent = "parent%i" % num
    parentCard = etree.Element("div")
    parentCard.set("class", "accordion")
    parentCard.set("id", parent)
    for action in actions:
        num = num + 1
        name = action.attrib['name']
        value = action.attrib['value']
        title = f"Actions: {name} [{value}]"
        card = createCardHeaderConditionAction(title, num)
        card = createCardBodyAction(action, card, parent, num)
        parentCard.append(card)
    cardBody.append(parentCard)
    return cardBody, num


def createCardBody(card, rule, num):
    carddivbody = etree.Element("div")
    carddivbody.set('id', 'collapse' + str(num))
    carddivbody.set('class', 'collapse')
    carddivbody.set('aria-labelledby', 'heading' + str(num))
    carddivbody.set('data-parent', '#accordion')

    cardbody = etree.Element("div")
    cardbody.set("class", "card-body")

    conditions = list(rule.iter("condition"))
    actions = list(rule.iter("action"))

    cardbody, num = createCardConditions(conditions, cardbody, num)
    cardbody, num = createCardActions(actions, cardbody, num)

    carddivbody.append(cardbody)
    card.append(carddivbody)
    return card, num


def createCardHeader(ruleName, num):
    card = etree.Element("div")
    cardheader = etree.Element("div")
    cardheader.set('id', 'heading' + str(num))
    h5 = etree.Element("h5")
    h5.set("class", "mb-0")

    button = etree.Element("button")

    button.set('data-toggle', 'collapse')
    button.set('data-target', '#collapse' + str(num))
    button.set('aria-expanded', 'false')
    button.set('aria-controls', 'collapse' + str(num))

    card.set("class", "card border")
    cardheader.set("class", "card-header")
    button.set('class', 'btn btn-light btn-group-toggle')

    h5.append(button)
    cardheader.append(h5)
    button.text = f"Rule: {ruleName}"
    card.append(cardheader)
    return card


def createCardsForRules(rules, accordion, body):
    num = 0

    for rule in rules:
        num = num + 1
        ruleName = rule.attrib['name']
        card = createCardHeader(ruleName, num)
        card, num = createCardBody(card, rule, num)
        accordion.append(card)
        body.append(accordion)
    return body


def getRules(question, rules, checkAllRules, libraryName, value):
    # Extract rules
    titleParam = ""
    if question == "From all the rules which ones import a risk pattern?":
        response = []
        for rule in rules:
            for action in rule.iter('action'):
                if action.attrib['name'] == "Import Risk Pattern":
                    rp = action.attrib['value'].split("_::_")[1]
                    if rp == value:
                        response.append(rule)
        rules = response
        title = f"Rules from all libraries to answer question: {question}: {value}"
        titleParam = value
    elif question == "From all the rules which ones check if a risk pattern exists?":
        response = []
        for rule in rules:
            for condition in rule.iter('condition'):
                if condition.attrib['name'] == "Risk pattern exists":
                    rp = condition.attrib['value'].split("_::_")[1]
                    if rp == value:
                        response.append(rule)
        rules = response
        title = f"Rules from all libraries to answer question: {question}: {value}"
        titleParam = value
    elif question == "Show all rules":
        title = f"Rules from all libraries"
    elif question == "For every library which rules use a specific answer?":
        response = []
        for rule in rules:
            for condition in rule.iter('condition'):
                if condition.attrib['name'] == "Question is answered":
                    if condition.attrib['value'] == value:
                        response.append(rule)
        rules = response
        title = f"Rules from the library {libraryName} that answer question: {question}:{value}"
        titleParam = value
    elif question == "Show all rules by library":
        title = f"Rules from the library {libraryName}"
    elif question == "What possible ways we have available for a specific risk pattern to appear in the model?":
        response = []
        for rule in rules:
            for condition in rule.iter('condition'):
                if condition.attrib['name'] == "Risk pattern exists":
                    rp = condition.attrib['value'].split("_::_")[1]
                    if rp == value:
                        response.append(rule)
            for action in rule.iter('action'):
                if action.attrib['name'] == "Import Risk Pattern":
                    rp = action.attrib['value'].split("_::_")[1]
                    if rp == value:
                        response.append(rule)
        rules = response
        title = f"Rules from all libraries to answer question: {question}: {value}"
        titleParam = value
    else:
        rules = []
        title = f"Wrong question {question}"
    return rules, title, titleParam


def createCollapseExpandButtons(body, root):
    collapse = etree.Element("button")
    collapse.text = "Collapse All"
    collapse.set("id", "collapse")

    expand = etree.Element("button")
    expand.text = "Expand All"
    expand.set("id", "expand")

    div = etree.Element("div")
    div.append(collapse)
    div.append(expand)
    div.set("style","justify-content: center;text-align: center;font-weight: bold;")

    body.append(div)

    script = etree.Element("script")
    script.text = '$("#collapse").click(function(){$("div[id^=\'collapse\']").removeClass("show");});$("#expand").click(function(){$("div[id^=\'collapse\']").addClass("show");});'
    root.append(script)

    return body


def createCardComponent(componentName, searchValue, num):
    card = etree.Element("div")
    cardheader = etree.Element("div")
    cardheader.set('id', 'headingComp' + str(num))
    h5 = etree.Element("h5")
    h5.set("class", "mb-0")

    button = etree.Element("button")

    button.set('data-toggle', 'collapse')
    button.set('data-target', '#collapseComp' + str(num))
    button.set('aria-expanded', 'false')
    button.set('aria-controls', 'collapseComp' + str(num))

    card.set("class", "card border")
    cardheader.set("class", "card-header")
    button.set('class', 'btn btn-light btn-group-toggle')

    h5.append(button)
    cardheader.append(h5)
    button.text = f"Component: {componentName} imports risk pattern {searchValue}"
    card.append(cardheader)

    return card


def createCardsForComponents(searchValue, components, accordion, body):
    num = 0
    if searchValue:
        for component in components:
            if searchValue in [i.attrib['ref'] for i in list(component.iter('riskPattern'))]:
                num = num + 1
                componentName = component.attrib['name']
                card = createCardComponent(componentName, searchValue, num)
                accordion.append(card)
                body.append(accordion)
    return body


def getComponents(question, searchValue, components):
    filteredComponents = []
    if searchValue and question in [questions[3], questions[5]]:
        for component in components:
            if searchValue in [i.attrib['ref'] for i in list(component.iter('riskPattern'))]:
                filteredComponents.append(component)
    return filteredComponents

def createBody(question, rules, components, body, root, checkAllRules, h1, value):
    rules, title, titleParam = getRules(question, rules, checkAllRules, h1, value)
    components = getComponents(question, value, components)
    title = title + " [ " + str(len(components)) + " components ][ " + str(len(rules)) + " rules ]"
    accordion = createTitleHtmlFile(title=title, body=body)
    body = createCollapseExpandButtons(body, root)
    createCardsForComponents(value, components, accordion, body)
    createCardsForRules(rules, accordion, body)
    titleQuestion = capitalizeFileName(question)
    return body, title, titleQuestion, titleParam


def generateRulesHtml(arrayLibrariesPaths, question, checkAllRules, value):

    titleParam = "NoParameters"
    base_html_path = Path.cwd() / "src" / "resources" / "changelog_base_html.html"
    parser = etree.HTMLParser()
    links = []

    # Returns answer to the questions for all rules in one single file
    if checkAllRules:
        file = etree.parse(str(base_html_path), parser)
        root = file.getroot()
        body = root.find("body")

        rules = []
        components = []
        for libraryPath in arrayLibrariesPaths:
            print("Checking "+str(libraryPath))
            treeroot = etree.parse(str(libraryPath)).getroot()
            rules = rules + list(treeroot.find('rules').iter('rule'))
            components = components + list(treeroot.find('componentDefinitions'))

        body, title, titleQuestion, titleParam = createBody(question, rules, components, body, root, checkAllRules, "All libraries", value)

        outFile_path = Path.cwd() / "outFiles" / "generatedHtml" / f"rules_{titleQuestion}_{capitalizeFileName(titleParam)}_AllLibraries.html"
        root.find("head").find("title").text = title
        writeToHtml(outFile_path, file.getroot())
        links.append(outFile_path)
    else:
        # Returns answer to the questions separated by libraries
        for libraryPath in arrayLibrariesPaths:
            file = etree.parse(str(base_html_path), parser)
            root = file.getroot()
            body = root.find("body")
            libraryName = str(os.path.splitext(os.path.basename(libraryPath))[0])
            treeroot = etree.parse(str(libraryPath)).getroot()

            components = list(treeroot.find('componentDefinitions'))
            rules = list(treeroot.find('rules').iter('rule'))

            body, title, titleQuestion, titleParam = createBody(question, rules, components, body, root, checkAllRules, libraryName, value)

            outFile_path = Path.cwd() / "outFiles" / "generatedHtml" / f"rules_{titleQuestion}_{capitalizeFileName(titleParam)}_{libraryName}.html"
            root.find("head").find("title").text = title
            writeToHtml(outFile_path, file.getroot())
            links.append(outFile_path)

    return links


def capitalizeFileName(filename):
    return re.sub(r'\W+', '', ''.join(x.capitalize() for x in filename.split(" ")))


# Usage:
# ToolKit: select libraries, question and parameters for that question in the GUI.
# Results are exported in outFiles/generatedHtml/rules_*.html
if __name__ == "__main__":
    if len(sys.argv) > 1:
        riskPattern = "DATASTORE"
        questionAnswered = "aws.sns.yes"
        question = questions[5]
        # TODO: Do this with opts
        generateRulesHtml(arrayLibrariesPaths=sys.argv[1:],
                          question=question,
                          checkAllRules=True,
                          value=riskPattern)
