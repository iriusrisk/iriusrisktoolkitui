import os
import logging
import src.sample_lib as supermod
from pathlib import Path
from src.common import getvalueFromMenu

logging.basicConfig(filename="logFile.log", 
                    format= '%(asctime)s  %(levelname)-10s %(message)s', 
                    datefmt =  "%Y-%m-%d-%H-%M-%S", 
                    filemode='w') 
  
#Creating an object 
logger=logging.getLogger() 
  
#Setting the threshold of logger to INFO 
logger.setLevel(logging.INFO) 

def removeExtraInfoFromExcel(string):
    string=str(string)
    string=string.replace("empty:u","")
    string=string.replace("text:u","")
    string=string[1:len(string)-1]
    return string

def generateHTML(xml_path, html_path):
    code="<!DOCTYPE html><html><head><title>Risk Patterns for "+xml_path.name+"</title><link rel=\"stylesheet\" href=\"https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css\" integrity=\"sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm\" crossorigin=\"anonymous\">"
    
    code=code+"<script src=\"https://code.jquery.com/jquery-3.3.1.slim.min.js\" integrity=\"sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo\" crossorigin=\"anonymous\"></script>"
    code=code+"<script src=\"https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js\" integrity=\"sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49\" crossorigin=\"anonymous\"></script>"
    code=code+"<script src=\"https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js\" integrity=\"sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy\" crossorigin=\"anonymous\"></script></head><body>"
   
    code+="<center><h2>Risk patterns for "+xml_path.name+"<h2></center>"
    
    
    rootClass = supermod.parse(str(xml_path), True)
    cont=0
    components=rootClass.get_components()
    code+="<div class=\"accordion\" id=\"components\">"
    codeComponent=""
    for component in components.get_component():
        weaknesses=component.get_weaknesses()
        controls=component.get_controls()
        usecases=component.get_usecases()
        codeUseCase="<div class=\"accordion\" id=\"usecases\">"
        for usecase in usecases.get_usecase():
            threats=usecase.get_threats()
            codeThreat="<div class=\"accordion\" id=\"threats\">"
            for threat in threats.get_threat():
                weaknessesThreat=threat.get_weaknesses()
                codeWeakness="<div class=\"accordion\" id=\"weaknesses\">"
                # Weaknesses and controls within
                addedControlsRefs = []
                for weaknessT in weaknessesThreat.get_weakness():
                    for weakness in weaknesses.get_weakness():
                        if weaknessT.get_ref() == weakness.get_ref():
                            weakName=weakness.get_name()
                            weakRef=weakness.get_ref()
                            weakDesc=weakness.get_desc()
                    controlsWeak=weaknessT.get_controls()
                    codeControl="<div class=\"accordion\" id=\"controls\">"
                    for controlW in controlsWeak.get_control():
                        for control in controls.get_control():
                            if controlW.get_ref() == control.get_ref():
                                addedControlsRefs.append(control.get_ref())
                                codeControl+=includeCard("controls", "Countermeasure","",control.get_name(), control.get_ref(), control.get_desc(),cont)
                                cont=cont+1
                    codeControl+="</div>"
                    codeWeakness+=includeCard("weaknesses", "Weakness", codeControl, weakName, weakRef, weakDesc,cont)
                    cont=cont+1
                codeWeakness += "</div>"
                codeWeakness += "<div class=\"accordion\" id=\"controlsWithoutWeaknesses\">"
                # Controls without weaknesses
                for control in threat.get_controls().get_control():
                    for controlNo in controls.get_control():
                        if control.get_ref() == controlNo.get_ref():
                            if control.get_ref() not in addedControlsRefs:
                                codeWeakness+=includeCard("controlsWithoutWeaknesses", "Countermeasure","",controlNo.get_name(), controlNo.get_ref(), controlNo.get_desc(),cont)
                                cont = cont + 1
                codeWeakness+="</div>"
                codeThreat+=includeCard("threats", "Threat", codeWeakness, threat.get_name(), threat.get_ref(), threat.get_desc(),cont)
                cont=cont+1
            codeThreat+="</div>"
            codeUseCase+=includeCard("usecases", "Use case", codeThreat, usecase.get_name(), usecase.get_ref(), usecase.get_desc(),cont)
            cont=cont+1
        codeUseCase+="</div>"
        codeComponent+=includeCard("components", "Risk pattern", codeUseCase, component.get_name(), component.get_ref(), component.get_desc(),cont)
        cont=cont+1
    codeComponent+="</div>"
    code+=codeComponent
    code+="</body></html>"

    fileHtml = open(str(html_path), "w")
    fileHtml.write(code)
    fileHtml.close()
    print("HTML file was generated in the path '%s'." %html_path)


def selectType(type):
    return {
        'Risk pattern': 'primary',
        'Use case': 'black',
        'Threat': 'danger',
        'Weakness': 'warning',
        'Countermeasure': 'success'
    }.get(type, 'dark')

def includeCard(levelParent, type, codeExtra, name, ref, desc, number):
    number=str(number)
    desc=str(desc)

    boxType=selectType(type)
    code="<div class=\"card border-"+boxType+"\"><div class=\"card-header \" id=\"heading"+number+"\"\>"
    code+="<h5 class=\"mb-0\">"
    code+="<button class=\"btn btn-link\" type=\"button\" data-toggle=\"collapse\" data-target=\"#collapse"+number+"\" aria-expanded=\"true\" aria-controls=\"collapse"+number+"\">"
    code+=type+": "+name+" <span>["+ref+"]</span>" 
    code+="</button></h5></div>"

    code+="<div id=\"collapse"+number+"\" class=\"collapse\" aria-labelledby=\"heading"+number+"\" data-parent=\"#"+levelParent+"\">"
    code+="<div class=\"card-body\">"+desc
    code+=codeExtra
    code+="</div></div></div>"
    return code

      
# We use this script to catch the arguments and run the principal method
def main():
    text="Please select one of the files to generate the HTML file (write the number) and press 'Enter':\n"
    libs_path=Path.cwd() / "libraries"

    libraries=os.listdir(str(libs_path))

    name_library=getvalueFromMenu(libraries, text)

    logger.info("INFO: Library selected: %s." %name_library)


    outputFile_path = Path.cwd() / "outFiles" / "generatedHtml" / name_library.replace(".xml", ".html")
    generateHTML(libs_path / name_library, outputFile_path)
    logger.info("INFO: Generated html file for the library: %s." %name_library)

if __name__ == '__main__':
    main()