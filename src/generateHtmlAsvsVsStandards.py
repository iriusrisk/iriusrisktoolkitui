import os
import sys
from lxml import etree, objectify

from moduleReadCsv import readCsvFile, getPath
home=os.getcwd()

def joinStandardListWithAsvs(standards, standardsInfo, asvsStandards):
    newStandards=list()
    for standard in standards:
        newStandard=list()
        found=False
        asvsFound=False
               
        for asvsStandard in asvsStandards:
            if standard[1] == asvsStandard[1]:
                newStandard.insert(0, asvsStandard[1])
                newStandard.insert(1, asvsStandard[2])
                newStandard.insert(2, asvsStandard[3])
                
        for standardInfo in standardsInfo:
            if standard[3] == standardInfo[1]:
                newStandard.insert(3, standardInfo[0])
                newStandard.insert(4, standardInfo[1])
                newStandard.insert(5, standardInfo[2])
                newStandard.insert(6, standardInfo[3])
                newStandard.insert(7, standardInfo[4])
                found=True
        if(found==False):
            newStandard.insert(3, "")
            newStandard.insert(4, "")
            newStandard.insert(5, "")
            newStandard.insert(6, "")
            newStandard.insert(7, "")
        newStandards.append(newStandard)
    return newStandards

def getAsvsRequirementsMappedWithStandard(standards):
    arrayOut=list()
    for standard in standards:
        if standard[7] == "x":
            arrayOut.append(standard)
    return arrayOut

def getAsvsRequirementsNotMappedWithStandard(standards):
    arrayOut=list()
    for standard in standards:
        if standard[7] != "x":
            standard[3]=""
            standard[4]=""
            standard[5]=""
            standard[6]=""
            standard[7]=""
            arrayOut.append(standard)
    return arrayOut

def generateHTML(standardName, standards):
    code="<!DOCTYPE html><html><head><title>Standard "+standardName+"</title><link rel=\"stylesheet\" href=\"https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css\" integrity=\"sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm\" crossorigin=\"anonymous\">"
    
    code=code+"<script src=\"https://code.jquery.com/jquery-3.3.1.slim.min.js\" integrity=\"sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo\" crossorigin=\"anonymous\"></script>"
    code=code+"<script src=\"https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js\" integrity=\"sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49\" crossorigin=\"anonymous\"></script>"
    code=code+"<script src=\"https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js\" integrity=\"sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy\" crossorigin=\"anonymous\"></script></head><body>"
   
    code+="<center><h2>Standard "+standardName+"</h2></center>"
    code+="<nav>"
    code+="<button class=\"btn btn-outline-success\" type=\"button\" data-toggle=\"collapse\" data-target=\"#collapseGroupExample1\" aria-expanded=\"false\" aria-controls=\"collapseGroupExample1\">Mapped with the standard</button>"
    code+="  "
    code+="<button class=\"btn btn-outline-warning\" type=\"button\" data-toggle=\"collapse\" data-target=\"#collapseGroupExample2\" aria-expanded=\"false\" aria-controls=\"collapseGroupExample2\">Not mapped with the standard</button>"
    code+="</nav><br/>"


    code+="<div class=\"accordion\" id=\"root\">"
    code+="<div class=\"collapse\" id=\"collapseGroupExample1\" data-parent=\"#root\">"
    code+=createTab(getAsvsRequirementsMappedWithStandard(standards),"Requirement ASVS", 'success')
    code+="</div>"
    code+="<div class=\"collapse\" id=\"collapseGroupExample2\" data-parent=\"#root\">"
    code+=createTab(getAsvsRequirementsNotMappedWithStandard(standards),"Requirement ASVS (Not mapped)", 'warning')
    code+="</div>"

    code+="</div>"
    code+="</body></html>"
    
    fileHtml = open(getPath("outFiles")+"/"+standardName+"_otherVersion.html", "w")
    fileHtml.write(code)
    fileHtml.close()



def includeCard(levelParent, type, codeExtra, name, ref, desc, number, color):
    number=str(number)
    desc=str(desc)

    
    code="<div class=\"card border-"+color+"\">"
    code+="<div class=\"card-body border-"+color+"text-"+color+"\" type=\"button\" data-toggle=\"collapse\" data-target=\"#collapse"+number+"\" aria-expanded=\"true\" aria-controls=\"collapse"+number+"\">\n"
    code+=type+": "+name+" <span>"
    if ref!="":
        code+="["+ref+"]"
    code+="</span>" 
    code+="</div>\n"

    code+="<div id=\"collapse"+number+"\" class=\"collapse\" aria-labelledby=\"heading"+number+"\" data-parent=\"#"+levelParent+"\">\n"
    code+="<div class=\"card-body border-"+color+"\">"+desc
    code+=codeExtra
    code+="</div>\n</div>\n</div>\n"
    return code

def createTab(standards, type, color):
    code="<div class=\"accordion\" id=\"standardGroup\">"
    if type == "Requirement ASVS":
        number=0
    if type == "Requirement ASVS (Not mapped)":
        number=1000
    if type == "Requirement ASVS (Not found but necessary)":
        number=2000
    lastStandard=""
    lastStandardGroup=""
    strandardCode=""
    strandardGroupCode="<div class=\"accordion\" id=\"standardGroup\">\n"
    for standard in standards:
        if(lastStandardGroup == ""):
            strandardCode="<div class=\"accordion\" id=\"standards\">\n"
            
        if(standard[1]!=lastStandardGroup) and lastStandardGroup != "":
            strandardCode+="</div>\n"
            strandardGroupCode+=includeCard("standardGroup", "Category",strandardCode, lastStandardGroup,"","",number, color)
            number=number+1
            strandardCode="<div class=\"accordion\" id=\"standards\">\n"
        if standard[2]!= lastStandard:
            controlCode="<div class=\"accordion\" id=\"controls\">\n"
        if standard[3] != "":
            controlCode+=includeCard("controls", "Requirement","",standard[5],standard[4],standard[6],number, color)
            number=number+1
        if standard[2]!= lastStandard:
            controlCode+="</div>\n"
                  
        strandardCode+=includeCard("standards", type ,controlCode, standard[2],standard[0],"",number, color)
        number=number+1

        
            
        lastStandardGroup=standard[1]
        lastStandard=standard[2]
                
                
    
    code+=strandardGroupCode
    code+="</div>\n</div>\n"
    return code

def main():
    if len(sys.argv) == 2:
        standardName=str(sys.argv[1])
        standardNameFile=standardName
        standardNameFile=standardNameFile.replace(" ","")
        standardNameFile=standardNameFile.replace(":","_")
        standardNameFileStandard="standard_"+standardNameFile
        standards=readCsvFile(getPath("inputFiles")+"/"+standardNameFileStandard+".csv")
        standardsInfo=readCsvFile(getPath("inputFiles")+"/"+standardNameFileStandard+"_info.csv")
        
        asvsStandards=readCsvFile(getPath("inputFiles")+"/standard_ASVS_3.0.1.csv")
        newStandards=joinStandardListWithAsvs(standards, standardsInfo, asvsStandards)
        
        pathOutput=home
        generateHTML(standardName, newStandards)
        print("Html file for the standard "+standardName+" was generated.")

if __name__ == '__main__':
    main()

