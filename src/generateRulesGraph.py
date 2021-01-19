#!/usr/bin/python
import sys
import xml.etree.ElementTree as ET
import networkx as nx
import json
import flask
from networkx.readwrite import json_graph


def getCondition(condition, componentDefinitions):
    cname = condition.attrib['name']
    group = 0
    if cname in ["Is specific component definition", "CONDITION_COMPONENT_DEFINITION"]:
        value = condition.attrib['value']
        if value in componentDefinitions.keys():
            message = "Is specific component definition: " + componentDefinitions[condition.attrib['value']]
        else:
            message = "Is specific component definition: " + value
        group = 0
    elif cname in ["Question Group exists", "CONDITION_QUESTION_GROUP_EXISTS"]:
        value = condition.attrib['value']
        message = "If question group '" + value + "' exists"
        group = 1
    elif cname in ["Question is answered", "CONDITION_QUESTION"]:
        value = condition.attrib['value']
        message = "If answer is " + value
        group = 2
    elif cname in ["Question is not answered", "CONDITION_QUESTION_NOT_ANSWERED"]:
        value = condition.attrib['value']
        message = "If answer is not " + value
        group = 9
    elif cname in ["Risk pattern exists", "CONDITION_RISK_PATTERN_EXISTS"]:
        value = condition.attrib['value']
        message = "Risk pattern " + condition.attrib['value'].split("_::_")[0] + " -> " + \
                  condition.attrib['value'].split("_::_")[1] + " exists"
        group = 3
    elif cname in ["Conclusion exists", "CONDITION_CONCLUSION_EXISTS"]:
        value = condition.attrib['value']
        message = "Conclusion " + value + " exists"
        group = 8
    elif cname in ["Conclusion not exists", "CONDITION_CONCLUSION_NOT_EXISTS"]:
        value = condition.attrib['value']
        message = "Conclusion " + value + " not exists"
        group = 12
    elif cname in ["Applied Countermeasure", "CONDITION_APPLIED_CONTROL"]:
        value = condition.attrib['value']
        message = "Countermeasure " + value + " is required"
        group = 13
    else:
        value = ""
        message = "Unknown: "+cname
    return value, message, group


def getActions(action, components):
    aname = action.attrib['name']
    print(aname)
    group = 0
    if aname in ["Insert Question Group", "INSERT_QUESTION_GROUP"]:
        valueList = action.attrib['value'].split("_::_")
        value = valueList[0]
        message = "Question: " + valueList[2]
        group = 4
    elif aname in ["Insert Question", "INSERT_QUESTION"]:
        valueList = action.attrib['value'].split("_::_")
        value = valueList[0]
        message = "Answer: " + valueList[1]
        group = 5
    elif aname in ["Import Risk Pattern", "IMPORT_RISK_PATTERN"]:
        valueList = action.attrib['value'].split("_::_")
        value = valueList[1]
        message = "Import Risk Pattern: " + components[valueList[1]]
        group = 6
    elif aname in ["Extend risk pattern", "EXTEND_RISK_PATTERN"]:
        valueList = action.attrib['value'].split("_::_")
        value = action.attrib['value']
        message = "Extend Risk Pattern " + valueList[0] + " >> " + valueList[1]
        group = 7
    elif aname in ["Insert Conclusion", "INSERT_CONCLUSION"]:
        valueList = action.attrib['value'].split("_::_")
        value = valueList[1]
        message = "Conclusion: " + valueList[2]
        group = 10
    elif aname in ["Apply Control", "APPLY_CONTROL"]:
        value = action.attrib['project'] + "_::_" + action.attrib['value']
        message = "Apply Control: " + action.attrib['project'] + " -> " + action.attrib['value']
        group = 11
    elif aname in ["Apply Security Standard", "APPLY_SECURITY_STANDARD"]:
        valueList = action.attrib['value'].split("_::_")
        value = valueList[1]
        message = "Apply security standard: " + value
        group = 12
    elif aname in ["Answer Question", "ANSWER_QUESTION"]:
        valueList = action.attrib['value'].split("_::_")
        value = valueList[0]
        message = "Anwsered question: " + value
        group = 13
    else:
        value = ""
        message = "Unknown: "+str(aname)
    return value, message, group


def generateGraph(rules, G, components, componentDefinitions):
    for rule in rules:
        conditions = []
        for condition in rule.iter('condition'):
            value, message, group = getCondition(condition, componentDefinitions)
            print(f'Adding node: "{value}":"{message}"')

            if not G.has_node(value):
                if message is "":
                    message = value
                G.add_node(value, message=message, group=group)
            conditions.append(value)

        for action in rule.iter('action'):
            value, message, group = getActions(action, components)
            if message is "":
                message = value
            G.add_node(value, message=message, group=group)

            for condition in conditions:
                # If value is null we have a problem :(
                G.add_edge(condition, value)
    return G


def generateRulesGraph(xmlPath, **kwargs):
    searchNode = kwargs.get('searchNode')
    depth = kwargs.get('depth')
    if depth:
        depth = int(depth)
    tree = ET.parse(xmlPath)
    root = tree.getroot()

    G = nx.DiGraph()
    components = {}
    componentDefinitions = {}

    for component in root.find('components').iter('component'):
        components[component.attrib['ref']] = component.attrib['name']

    for component in root.find('componentDefinitions').iter('componentDefinition'):
        componentDefinitions[component.attrib['ref']] = component.attrib['name']

    # rules = []
    # if searchNode and depth:
    #     print(f"Searching {searchNode} with depth {depth}")
    #     ids = []
    #     searchPath = {searchNode}
    #     for i in range(0, depth):
    #         print("Level "+str(i))
    #         print(searchPath)
    #         for rule in root.find('rules').iter('rule'):
    #             con = False
    #             act = False
    #             for condition in rule.iter('condition'):
    #                 value, message, group = getCondition(condition, componentDefinitions)
    #                 if value in searchPath and rule not in rules:
    #                     rules.append(rule)
    #                     con = True
    #                 ids.append(value)
    #             for action in rule.iter('action'):
    #                 value, message, group = getActions(action, components)
    #                 if value in searchPath and rule not in rules:
    #                     rules.append(rule)
    #                     act = True
    #                 ids.append(value)
    #             if con or act:
    #                 for var in ids:
    #                     searchPath.add(var)
    #             else:
    #                 ids = []
    #
    #
    # else:
    #     print("All nodes")
    #     rules = list(root.find('rules').iter('rule'))
    print("All nodes")
    rules = list(root.find('rules').iter('rule'))
    print(len(rules))

    G = generateGraph(rules, G, components, componentDefinitions)

    if searchNode is not "" and depth >= 0:
        print("searching node " + searchNode)
        ids = {searchNode}
        newEdges = []
        for i in range(0, depth):
            for edge in G.edges:
                source, target = edge
                if source in ids:
                    ids.add(target)
                    newEdges.append(edge)
                elif target in ids:
                    ids.add(source)
                    newEdges.append(edge)
                else:
                    pass

        H = nx.DiGraph()
        H.add_edges_from(newEdges)
        for node in list(G.nodes.data()):
            if node[0] in ids:
                H.add_node(node[0], message=node[1]['message'], group=node[1]['group'])

        d = json_graph.node_link_data(H)
    else:
        d = json_graph.node_link_data(G)
    json.dump(d, open('../outFiles/graph/graph.json', 'w+'))

    app = flask.Flask(__name__, static_folder="../outFiles/graph")
    app.config["CACHE_TYPE"] = "null"

    @app.route('/')
    def static_proxy():
        return app.send_static_file('index.html')

    app.run(port=8000)


def main():
    searchNode = ""
    depth = ""
    if len(sys.argv) == 2 and sys.argv[1].endswith(".xml"):
        xmlPath = sys.argv[1]
    elif len(sys.argv) == 4:
        xmlPath = sys.argv[1]
        searchNode = sys.argv[2]
        depth = sys.argv[3]
    else:
        print("This script prints the relations between rules in a library. "
              "Graph can be generated full (without parameters) "
              "or scoped (defining node to watch and depth to backtrack)")
        print("Graph will be served in a default Flask server (127.0.0.1:8000)")
        print("Usage: python generateRulesGraph.py <library.xml> [<nodeId> <depth>]")
        print("Examples: ")
        print("python generateRulesGraph.py /path/to/CS-Default.xml")
        print("python generateRulesGraph.py /path/to/CS-Default.xml CS-Default_::_DATASTORE 3")
        print("python generateRulesGraph.py /path/to/CS-Default.xml bespokeCrypto 1")
        return
    generateRulesGraph(xmlPath, searchNode=searchNode, depth=depth)


if __name__ == '__main__':
    main()
