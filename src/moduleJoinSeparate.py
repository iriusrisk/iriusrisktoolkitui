import os
from os import listdir
import sys
home=os.getcwd()
import src.xmlValidator as validation
from pathlib import Path
LOCAL_PATH=Path.cwd().parents[0]
###############################################################
### First, I have got the functions of the joinFiles script ###
###############################################################
# Remove de default values in the xml file
def deleteContent(pfile):
    pfile.seek(0)
    pfile.truncate()


# Get the xml file info (controls, weaknesses, threats) from a file in a determinate path (Method for the join files method)
# - First, we get the files in the path.
# - We check if the path is empty and there is no files in the folder. Write in the document the tag with empty values
# - If there are files, write the correspond tags in the document and open each file and add the information from the files to the document.
def readRiskPattern(path, tag, projectFile):
    listdir = os.listdir(str(path))
    if len(listdir) == 0:
        projectFile.write('<'+tag+' />\n') 
    else:
        projectFile.write('<'+tag+'>\n')
        for it in listdir:
            file = open(str(path / it),'r', encoding='utf-8')
            projectFile.write(file.read())
            file.close()
        
        projectFile.write('\n</'+tag+'>\n')
# Get the xml file info from a file (usecases with the threats) in a determinate path (Method for the join files method)
# - First, we get the files in the path.
# - We check if the path is empty and there is no files in the folder. Write in the document the tag with empty values
# - If there are files, write the correspond tags in the document and open each file and add the information from the files to the document.
# - In this case, each use case has got threats. Therefore, we also add all information about the threats into the document.
def readUseCases(pathComponent, projectFile):    
    listdirUseCases = os.listdir(str(pathComponent / 'usecases'))
    if len(listdirUseCases) == 0:
        projectFile.write('<usecases />\n') 
    else:
        projectFile.write('<usecases>\n')
        for it in listdirUseCases:
            fileUseCases = open(str(pathComponent / 'usecases' / it / 'usecase.xml'),'r')
            projectFile.write(fileUseCases.read())
            fileUseCases.close()
            # We get all data of threats in the next path
            readRiskPattern(pathComponent / 'usecases' / it / 'threats','threats',projectFile)   
            projectFile.write('</usecase>\n') 

        projectFile.write('</usecases>\n')

# We join all information about the risk pattern into each component (Method for the join files method)
# - First, we get the files in the path.
# - We get each component data and also the data of its usecases, threats, weaknesses and countermeasures.
# - We add all these data to the document
def readComponents(pathComponents, projectFile):
    projectFile.write('<components>\n')
    listdir = os.listdir(str(pathComponents))
    for it in listdir:
        fileComp = open(str(pathComponents / it / 'component.xml'),'r')
        a= fileComp.read()
        projectFile.write(a)
        readRiskPattern(pathComponents / it /'weaknesses','weaknesses', projectFile)
        readRiskPattern(pathComponents / it / 'controls','controls', projectFile)
        readUseCases(pathComponents / it, projectFile)
        projectFile.write('</component>\n')

    projectFile.write('</components>\n')


# This is a functionality for the tests and it return an array with the ids from one tag.
def getArrayByTag(string,tag):
    array=[]
    num=0
    while(string.find("<"+tag+" ref='") != -1):
        string = string[string.find("<"+tag+" ref='")+7+len(tag):]
        if string.find("'") != -1:
            posFin = string.find("\'")
            array.insert(num,string[0:posFin])
            string = string[string.find("'")+1:]
            num=num+1
    return array

# Returns an array with the refs of all elements by tag from one component.
def getArrayByTagPerComponent(string,tag):
    # - If the tag is control or weakness, we shall remove from the string the use cases to avoid duplicated controls or duplicated weaknesses
    if tag == "control":
        if string.find("<usecases />")!=-1:
            string=string[0:string.find("<usecases />")]
        else:
            string=string[0:string.find("<usecases>")]
            
    if tag == "weakness":
        if string.find("<usecases />")!=-1:
            string=string[0:string.find("<usecases />")]
        else:
            string=string[0:string.find("<usecases>")]
    
    # - We get all references of each tag element and add to the returned array
    array=[]
    num=0
    while(string.find("<"+tag+" ref='") != -1):
        string = string[string.find("<"+tag+" ref='")+7+len(tag):]
        if string.find("'") != -1:
            posFin = string.find("\'")
            array.insert(num,string[0:posFin])
            string = string[string.find("'")+1:]
            num=num+1
    return array

# With this method, we compare two files, with the number of components, usecases, threats, weaknesses, controls. 
# And we review the integrity of the files with a XSD Schema verification. 
# We return and String with the information about where are the errors.
def compareFiles(libraryPath_library, libraryPath_joined, xsd_library):
    origin = open(str(libraryPath_library),'r').read()
    destination = open(str(libraryPath_joined),'r').read()
    errors=[]               
    if len(getArrayByTag(origin, "component")) != len(getArrayByTag(destination, "component")):
        errors.append("Components")
    if len(getArrayByTag(origin, "usecase")) != len(getArrayByTag(destination, "usecase")):
        errors.append("Use Cases")
    if len(getArrayByTag(origin, "threat")) != len(getArrayByTag(destination, "threat")):
        errors.append("Threats")
    if len(getArrayByTag(origin, "weakness")) != len(getArrayByTag(destination, "weakness")):
        errors.append("Weaknesses")
    if len(getArrayByTag(origin, "control")) != len(getArrayByTag(destination, "control")):
        errors.append("Controls")
    if (validation.xmlValidator(libraryPath_library, LOCAL_PATH / "inputFiles" / "XSD_Schema" / "library.xsd")==False):
        errors.append("XSD Schema original library")
    if (validation.xmlValidator(libraryPath_joined, LOCAL_PATH / "inputFiles"/"XSD_Schema"/ "library.xsd")==False):
        errors.append("XSD Schema joined library")
    if len(errors) == 0:
        return True
    else:        
        msg="There are not the same number of "
        for error in errors:
            if msg == "There are not the same number of ":
                msg= msg+" "+error
            else:
                msg= msg+", "+error
        print("ERROR: "+msg+".\n")
        return False

# The first function to run the principal functions of the script
def joinFiles(separatedPath, parts):
    # we check if a folder of the library exist, if it doesn't exist, we launch the method to separate the library in files
    joined_path=separatedPath.parents[0].parents[0] / "joinedLibraries"
    libraryFile=separatedPath.parents[0].parents[0].parents[0]/"libraries" / str(separatedPath.name + ".xml")
    if not os.path.exists(str(joined_path)):
        os.mkdir(str(joined_path))

    if not os.path.exists(str(libraryFile)):
        separateFiles(separatedPath, libraryFile, parts)
    # Open the new library file and remove the current content
    projectFile = open(str(joined_path / str(separatedPath.name+".xml")),'w')
    deleteContent(projectFile)
    
    # open each file from the library folder and the sub folders and add the data to the new library file
    fileaux=open(str(separatedPath / "project.xml"),'r')
    projectFile.writelines(fileaux.read ())
    fileaux.close()
    if(parts == "riskPatterns"):
        readComponents(separatedPath / 'components' , projectFile)
        projectFile.write('<rules/>\n')
    if(parts == "rules"):
        projectFile.write('<components/>\n')
        readRiskPattern(separatedPath / 'rules','rules', projectFile)
    if(parts == ""):
        readComponents(separatedPath / 'components', projectFile)
        readRiskPattern(separatedPath / 'rules','rules', projectFile)
    projectFile.writelines('\n</project>')

    projectFile.close()
    output_path=joined_path / str(separatedPath.name+".xml")
    text="Library joined in one file successfully in the path '%s'.\n"%output_path

    return text, output_path

####################################################################
### Second, I have got the functions of the separateFiles script ###
####################################################################


# With this function, we get the name from a xml tag
def getName(string):
    name=string[string.find("name=")+6:]
    if string.find("name='")!=-1:
        name=name[0:name.find("'")]
    if string.find("name=\"")!=-1:
        name=name[0:name.find("\"")]   
    name=name.replace("/","_")
    return name

# With this function, we create a new folder if it doesn't exist
def createFolder(directory_path):
    try:
        os.stat(str(directory_path))
    except:
        os.mkdir(str(directory_path))
         
# To filter the Component Detail if the Risk Pattern is empty or not
def getComponentDetail(string):
    if string.find("<weaknesses>") != -1:
        return string[0:string.find("<weaknesses>")]
    if string.find("<weaknesses />") != -1:
        return string[0:string.find("<weaknesses />")]    
    if string.find("<weaknesses/>") != -1:
        return string[0:string.find("<weaknesses/>")]  
    else: 
        return ""



# With this function, we create a new file, we open it, we write it and we close it.
def createFile(string, filePath):
    filePath=str(filePath)
    file = open(filePath,'w')
    file.write(string)
    file.close()
    
# With this function, we convert the singular tag to the plural tag.
def convertingToEnding(tag):
    if tag == "weakness":
        return "weaknesses"
    if tag == "control":
        return "controls"
    if tag == "usecase":
        return "usecases"
    if tag == "threat":
        return "threats"
    if tag == "component": 
        return "components"
    if tag == "rule":
        return "rules"

# With this function, we find each component and we return an array with the string for each component
def getComponents(string):
    components = []
    cont = 1
    while (string.find("<component ") != -1):  
        posInit = string.find("<component ")
        posEnd = string.find("</component>")+13
        components.append(string[posInit:posEnd])
        string=string[posEnd:]
        cont=cont+1

    return components
# With this function, we find each usecase and we return an array with the string for each usecase from a determinate component
def getUseCasesByTag(string):
    usecases = []
    cont = 1
    if(string.find("<usecases")!=-1):
        if(string[string.find("<usecases"):string.find("<usecases")+10]=="<usecases>"):
            string=string[string.find("<usecases>")+10:]
            while (string.find("<usecase") != -1):  
                posInit = string.find("<usecase")
                if(string[posInit:10]=="<usecase/>"):
                    posEnd = string.find("<usecase/>")
                else:
                    if(string[posInit:11]=="<usecase />"):
                        posEnd = string.find("<usecase />")
                    else:
                        posEnd = string.find("</usecase>")+11
                if string[posInit:posEnd]!="":
                    usecases.append(string[posInit:posEnd])
                string=string[posEnd:]
                cont=cont+1

    return usecases
# With this function, we find the correspond tag and we create the correspond file with the correspond information (For example, threats, weaknesses and controls)
def getDetailsByTag(stringInit,tag,folder):
    if stringInit.find("<"+convertingToEnding(tag)) != -1:
        tagToVerify=stringInit[stringInit.find("<"+convertingToEnding(tag)):stringInit.find(">")+1]
        if(tagToVerify=="<"+convertingToEnding(tag)+" />"):
            return stringInit[stringInit.find("<"+convertingToEnding(tag)+" />")+len(convertingToEnding(tag))+4:]
        if(tagToVerify=="<"+convertingToEnding(tag)+"/>"):
            return stringInit[stringInit.find("<"+convertingToEnding(tag)+"/>")+len(convertingToEnding(tag))+4:]
        else:       
            string=stringInit[stringInit.find("<"+convertingToEnding(tag)+">"):stringInit.find("</"+convertingToEnding(tag)+">")+len(convertingToEnding(tag))+3]
            while (string.find("<"+tag+" ") != -1):  
                posInit = string.find("<"+tag+" ")
                posEnd = string.find("</"+tag+">")+len(tag)+3
                name=getName(string)
                # We remove the content data of the rule
                if tag == "rule":
                    ruleString=string[posInit:posEnd]+"\n"
                    #ruleString=ruleString[0:ruleString.find("<content>")]+"<content />"+ruleString[ruleString.find("</content>")+10:]
                    createFile(ruleString,folder / str(name+'.xml'))
                else:
                    createFile(string[posInit:posEnd],folder / str(name+'.xml'))

                string=string[posEnd:]

            stringInit=stringInit[stringInit.find("</"+convertingToEnding(tag)+">")+len(convertingToEnding(tag))+3:]
            return stringInit

# This is the principal function was launched, and we create the first folder and files with the correspond information, and we call the other functions.
def separateFiles(folder, library_path,  parts):
    # We create the principal folder and the document for the project
    
    if os.path.exists(str(folder)):
        removeAll(folder)
    createFolder(folder)
    projectFile = open(str(library_path),'r')

    readFile = projectFile.read()
    
    # We create the folder components and if there are componets we create a folder per component, and a file with the information for each domponent
    
    createFolder(folder / 'components')
    if(readFile.find("<components>")==-1):
        if(readFile.find("<components />")!=-1):
            createFile(readFile[0:readFile.find("<components />")],folder/'project.xml')
        else:
            createFile(readFile[0:readFile.find("<components/>")],folder / 'project.xml')
    else:
        createFile(readFile[0:readFile.find("<components>")],folder / 'project.xml')
    
    line=readFile[readFile.find("<components>")+12:]
    if(parts == "" or parts == "riskPatterns"):
        componentInfo =line[0:line.find("</components>")+13]
        # We get a list of components(the data of each component is recopiled as string)
        components=getComponents(componentInfo)
        # We get each component and create the correspond folder
        for component in components:
            componentName = getName(component)
            createFolder(folder / 'components' / componentName)
            # In the component folder, we create a file with the data about the component and we create the folders for use cases, weaknesses and controls
            createFile(getComponentDetail(component), folder / 'components' / componentName / 'component.xml')
            
            createFolder(folder / 'components' / componentName / 'weaknesses')
            createFolder(folder / 'components' / componentName / 'controls')
            createFolder(folder / 'components' / componentName / 'usecases')
            # We create a file per weakness and add the data about each weakness into the file.
            component=getDetailsByTag(component,'weakness',folder / 'components' / componentName / 'weaknesses')
            # We create a file per control and add the data about each control into the file.
            component=getDetailsByTag(component,'control',folder / 'components' / componentName / 'controls')
            # We get all use cases per component
            usecases = getUseCasesByTag(component)
            for usecase in usecases:
                # we create a file per use case with the data about each use cases
                usecaseName = getName(usecase)
                createFolder(folder / 'components' / componentName / 'usecases' / usecaseName)
                if usecase.find("<threats>") == -1:
                    if(usecase.find("<threats />") != -1):
                        createFile(usecase[0:usecase.find("<threats />")],folder / 'components' / componentName / 'usecases'/ usecaseName / 'usecase.xml')
                    if(usecase.find("<threats/>") != -1):
                        createFile(usecase[0:usecase.find("<threats/>")],folder / 'components' / componentName / 'usecases' / usecaseName / 'usecase.xml')
                else:
                    createFile(usecase[0:usecase.find("<threats>")],folder / 'components' / componentName / 'usecases' / usecaseName / 'usecase.xml')
                # If there are threats we create the folder "threats" per each use case and add the data of each threat in the correspond file per threat
                createFolder(folder / 'components' / componentName / 'usecases' / usecaseName / 'threats')
                component=getDetailsByTag(usecase,'threat',folder / 'components' / componentName / 'usecases' / usecaseName / 'threats')

     
    # We get all data of the rules, create the folder rules and create a file for each rule with all data about the correspond rule.
    ruleLines=readFile[readFile.find("<rules>"):readFile.find("</rules>")+8]
    createFolder(folder / 'rules')
    if(parts == "" or parts == "rules"):
        getDetailsByTag(ruleLines,'rule',folder/'rules')
    text="Library separate in several files and folders successfully in the path '%s'.\n"%folder
    return text

# With this method, we remove the old folders and files
def removeAll(path):
    if os.path.exists(str(path)):
        for i in os.listdir(str(path)):
            if os.path.isfile(str(path / i)):
                os.remove(str(path / i))
            if os.path.isdir(str(path / i)):
                removeAll(path / i)
                if os.path.exists(str(path / i)):
                    os.rmdir(str(path / i))
        os.rmdir(str(path))

# Return an array with the component name and the tag elements to verify if there is duplicated ids or elements
# (This method is used in the tests and for one verification)
def verifyTagForComponent(string,tag):
    array=[]
    arrayAux=[]
    line=string[string.find("<components>")+12:]    
    componentInfo =line[0:line.find("</components>")+13]
    # We get all components from the string
    components=getComponents(componentInfo)
    # If the tag is component, we return all ref components that there are cointained in the string
    if tag == "component":
        before = ""
        # We get all ref of the components and add the refs to one array
        for component in components:
            componentRef=component[component.find("<component ref=")+16:]
            componentRef=componentRef[0:componentRef.find("\'")]
            arrayAux.append(componentRef)
        # we sort the ref array
        arrayAux=sorted(arrayAux)
        for i in arrayAux:
            if i == before:
                array.append(i)
            before=i
    else:           
        for component in components:
            before=""
            componentName = getName(component)
            # if the tag is threat, we loop all use cases and get all threats per each use case, and add to one array with the component name and the ref of threat
            if tag == "threat":
                usecases = getUseCasesByTag(component)
                for usecase in usecases:
                    arrayAux = getArrayByTag(usecase,tag)
                    arrayAux=sorted(arrayAux)
                    for i in arrayAux:
                        if i == before:
                            array.append(componentName+" - "+i)
                        before=i
            else:  # If the tag is usecase, weakness or control, we get all tag elements and add the component name and the ref of the tag element              
                arrayAux = getArrayByTagPerComponent(component,tag)
                arrayAux=sorted(arrayAux)
                for i in arrayAux:
                    if i == before:
                        array.append(componentName+" - "+i)
                    before=i          
    return array
# In this method, we check if all tags are correct and if there is no problem we return true
def inputFileVerificationAll(fileName):
    result = False
    file_path=home+'/'+fileName+".xml"
    if os.path.isfile(file_path):
        projectFile = open(file_path,'r')
        xmlString = projectFile.read()
        if(len(verifyTagForComponent(xmlString,"component"))==0):
            if(len(verifyTagForComponent(xmlString,"weakness"))==0):
                if(len(verifyTagForComponent(xmlString,"control"))==0):
                    if(len(verifyTagForComponent(xmlString,"usecase"))==0):
                        if(len(verifyTagForComponent(xmlString,"threat"))==0):
                            result = True
    else:
        print("The File doesn't exist.")
    return result

# In this method, we compare two arrays and we return an array with the differences
def compareFilesToString(orig, dest):
    found = False
    results = []
    # We get the bigger array as first array and the second array is the smaller
    if len(orig) < len(dest):
        firstArray = dest
        secondArray = orig
    else:
        firstArray = orig
        secondArray = dest
    contFirst=0
    contSecond=0
    # We compare both array, and if one item is not found in both array, we add it to a new array of results andwe return this array.
    while(contFirst < len(firstArray)):
        contSecond=0
        while(contSecond < len(secondArray)):
            found=False
            if(firstArray[contFirst] == secondArray[contSecond]):
                found=True
                break
            else:
                contSecond=contSecond+1
        if(found==False):
            results.append(firstArray[contFirst])
        contFirst=contFirst+1
    return results

# We convert an array to one string to show the test results
def convertArrayToString(array):
    value=""
    for idx, val in enumerate(array):
        if idx == 0:
            value=str(val)
        else:
            value=value+", "+str(val)
    return value

# When the number of parameter are not correct, we launch a help
def showHelp():
    print("--------------------------------- HELP ---------------------------------")
    print("")
    print("To use this script, we need to give two or three args.")
    print(" For the first arg, there are two options:")
    print("  - 'join': we join the files from the folder of the second arg ")
    print("            into a new file, this file is stored in the folder 'joinedLibraries'")
    print("  - 'separate': we separate the file from the second arg and we ")
    print("               generate the folders and files with the information.")
    print("")
    print(" For the second arg, we have to give the name of the folder to generate")
    print(" new files for the 'join' script or the name of the file to generate")
    print(" the files and folders for the 'separate' script")
    print("")
    print(" For the third arg,there are two options:")
    print("  - 'riskPatterns': we separate or join only the risk patterns. ")
    print("  - 'rules': we separate or join only the rules.")
    print("")
    print(" For example, we run the script as:")
    print("  python3 generateLibrary.py join example")
    print("  or")
    print("  python3 generateLibrary.py join example rules")
    print("")
