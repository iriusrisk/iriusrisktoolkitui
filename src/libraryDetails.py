import os
from lxml import etree, objectify
import sys
home=os.getcwd()
from pathlib import Path
import src.sample_lib as sl
import pandas as pd

def readInfoFromXml(lib_path, columns):
    data=list()
    root = sl.parse(str(lib_path), silence=True)
    for component in root.get_components().get_component():
        sizeWeaks=len(component.get_weaknesses().get_weakness())
        sizeControls=len(component.get_controls().get_control())
        sizeUseCases=len(component.get_usecases().get_usecase())
        sizeThreats=0
        for usecase in component.get_usecases().get_usecase():
            sizeThreats+=len(usecase.get_threats().get_threat())
        data.append([root.get_name(), component.get_name(), sizeUseCases, sizeThreats, sizeWeaks, sizeControls])
    
    data= pd.DataFrame(data, columns=columns)
    array=[[root.get_name(), "TOTAL:", data[columns[2]].sum(), data[columns[3]].sum(), data[columns[4]].sum(), data[columns[5]].sum()]]
    dfm=pd.DataFrame(array, columns=columns)
    data=data.append(dfm)
    
    return data


def readInfoFromProductXml(path, columns):
    data = list()
    root = etree.parse(str(path)).getroot()

    trustzones = dict()
    for trustzone in root.find("trustZones").iter("trustZone"):
        trustzones[trustzone.attrib['ref']] = trustzone.attrib['name']

    for component in root.iter("component"):
        for trustzone in component.iter("trustZone"):
            tzName = trustzones[trustzone.attrib['ref']]
        compName = component.attrib['name']
        totalControls = 0
        totalRequired = 0
        totalImplemented = 0
        for control in component.find("controls").iter("control"):
            if control.attrib['state'] == "Required":
                totalRequired += 1
            elif control.attrib['state'] == "Implemented":
                totalImplemented += 1
            totalControls += 1

        data.append([root.attrib['name'], tzName, compName, totalControls, totalImplemented, totalRequired])
    data = pd.DataFrame(data, columns=columns)

    return data


def showLibraryDetails():
    pathLibs= Path.cwd() / "libraries"
    text="Select the number of the library to show the details:\n"
    libs=os.listdir(str(pathLibs))
    for lib in libs:
        if lib.endswith(".xml"):
            text+="%i - %s.\n"%(libs.index(lib), lib)

    try:
        value=int(input(text))
        readInfoFromXml(str(pathLibs / libs[value]))
    except:
        print("The introduced value is wrong!!")


def main2():
    if len(sys.argv) != 2:
        print("You should pass more args!!")
        print("")
    else:
        fileName=str(sys.argv[1])
        if(fileName.find(".xml")!=-1):
            fileName=fileName.replace(".xml","")
        readInfoFromXml(home+"/"+fileName+".xml")
        print("The script has finished!!")

def main():
    fileName="collesprod"
    readInfoFromProductXml(home+"/../products/"+fileName+".xml", ['Product Name', 'Trust Zone', 'Component', '# Countermeasures', '# Implemented', '# Required'])

if __name__ == '__main__':
    main()