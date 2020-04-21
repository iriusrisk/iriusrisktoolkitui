import os
from lxml import etree, objectify
from moduleReadCsv import getPath
home=os.getcwd()

def main():
    asvsData = getAsvsDataFromCsv()
    controlsData = getControlsData()
    printAsvsVsControls(asvsData, controlsData)



def getAsvsDataFromCsv():
    asvsData = list()
    file = open(getPath("inputFiles")+"/standard_ASVS_3.0.1.csv",'r')
    data = file.read()

    while(data.find("\n")!=-1):
        arrayList=list()
        processData=data[0:data.find("\n")]
        data=data[data.find("\n")+1:]
        while(processData.find("||")!=-1):
            value=processData[0:processData.find("||")]
            processData=processData[processData.find("||")+2:]
            arrayList.append(value)

        value=processData[0:processData.find("\\")]
        arrayList.append(value)
        asvsData.append(arrayList)
    return asvsData


def getControlsData():
    controls=list()
    path_libs=Path.cwd() / "libraries"
    libraries =os.listdir(str(path_libs))
    for lib in libraries:
        if lib.endswith(".xml"):
            print("Library read: "+lib)
            xml_doc = etree.parse(str(path_libs / lib))
            root = xml_doc.getroot()
            for i in root:
                if i.tag == "components":
                    components=i
            for component in components:
                for b in component:
                    if b.tag == "controls":
                        contrls=b
                for contrl in contrls:
                    controlName=contrl.attrib.get('name')
                    controlRef=contrl.attrib.get('ref')
                    controlDesc=str(contrl[0].text)
                    standards=contrl[3]
                    if len(standards)>0:                                         
                        for standard in standards:
                            if standard.attrib.get('supportedStandardRef')=="OWASP-ASVS-Level-3":
                                controls.append([standard.attrib.get('ref'),standard.attrib.get('supportedStandardRef'), controlRef,controlName,controlDesc])
    controls=sorted(controls,key=lambda x: x[0])
    controlBefore=""
    standardBefore=""
    uniqueControls= list()

    
    for c in controls:
        found = False
        for u in uniqueControls:
            if c[0] == u[0] and c[2] == u[2]:
                found=True
                
        if found == False:
            uniqueControls.append(c)
    
    return uniqueControls
def printAsvsVsControls(asvsData, controlsData):
    
    code="<!DOCTYPE html><html><head><title>Mapping OWASP ASVS v3.0.1 requirements vs Irius risk countermeasures</title><link rel=\"stylesheet\" href=\"https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css\" integrity=\"sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm\" crossorigin=\"anonymous\">"
    
    code=code+"<script src=\"https://code.jquery.com/jquery-3.3.1.slim.min.js\" integrity=\"sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo\" crossorigin=\"anonymous\"></script>"
    code=code+"<script src=\"https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js\" integrity=\"sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49\" crossorigin=\"anonymous\"></script>"
    code=code+"<script src=\"https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js\" integrity=\"sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy\" crossorigin=\"anonymous\"></script></head><body>"
    code=code+"<div id=\accordion\">"
    for i in asvsData:
        req=i[0]
        if req !="#":
            req="Requirement "+req
            nameReq=i[2]    
            if i[7] == "x":
                
                code=code+"<div class=\"card text-white bg-success mb-3\"><div class=\"card-header\"><h4>["+req+"] "+nameReq+"</h4></div><div class=\"card-body\">"
            else:
                code=code+"<div class=\"card text-white bg-warning mb-3\"><div class=\"card-header\"><h4>["+req+"] "+nameReq+"</h4></div><div class=\"card-body mb-3\">"
            for j in controlsData:
                if j[0] == i[0]:
                    print("Requirement found: "+j[0]+" - Countermeasure: "+j[2])
                    code=code+"<div class=\"card border-success text-dark bg-light mb-3\" >"
                    controlValue="["+str(j[2])+"] "+str(j[3])
                    code=code+"<h5 class=\"card-text text-success\">"+controlValue+"</h5>"
                    if j[4] != "":
                        code=code+"<div class=\"card border-success\">"
                        code=code+"<p class=\"card-text\">"+str(j[4])+"</p>"
                        code=code+"</div>"
                    code=code+"</div>"
            code=code+"</div></div>"
    code=code+"</div>"

    endCode="</body></html>"
    file = open(home+"/comparationASVSvsCountermeasures.html",'w')
    file.write(code+endCode)
    file.close()

#if __name__ == '__main__':
 #   main()
main()