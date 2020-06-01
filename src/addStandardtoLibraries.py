import os
import src.sample_lib as sl
import pandas as pd
from lxml import etree
from src.xmlValidator import xmlValidator
from pathlib import Path
from src.convertCrlfToLf import convertCRLFtoLF

from src.common import exportLib2XML
import logging

home=os.getcwd()
logging.basicConfig(filename="logFile.log",
                    format= '%(asctime)s  %(levelname)-10s %(message)s',
                    datefmt =  "%Y-%m-%d-%H-%M-%S",
                    filemode='w')

#Creating an object
logger=logging.getLogger()

#Setting the threshold of logger to INFO
logger.setLevel(logging.INFO)


def createStandard(supportedStandardRef, standardRef):
    standardClass = sl.standardType()
    return standardClass.factory(supportedStandardRef=supportedStandardRef,
    ref=standardRef)


def searchControls(library_path, supportedStandard_name, standard_file_path):
    rootObj = sl.parse(str(library_path), silence=True)

    supportedStandards=rootObj.get_supportedStandards()
    components=rootObj.get_components().get_component()


    supportedStandardCreated = False

    dfm = pd.read_csv(str(standard_file_path), sep="|")
    dfm.columns=['Standard ASVS', "Ref ASVS", "Supported Standard Name", "Supported Standard Ref", "Standard Ref"]

    for index, row in dfm.iterrows():
        asvs_supportedStandardRef=row.get("Standard ASVS")
        asvs_ref=str(row.get("Ref ASVS"))
        supportedStandard_name=row.get("Supported Standard Name")
        supportedStandardRef=row.get("Supported Standard Ref")
        standardRef=row.get("Standard Ref")
        for component in components:
            controls=component.get_controls().get_control()
            for control in controls:
                standards = control.get_standards()
                for standard in standards.get_standard():

                    if standard.get_supportedStandardRef()==asvs_supportedStandardRef:
                        if standard.get_ref()==asvs_ref:
                            alreadyExist=False
                            for stard in standards.get_standard():
                                if stard.get_supportedStandardRef() == supportedStandardRef and stard.get_ref() == standardRef:
                                    alreadyExist=True
                            #construir standard y añadirlo
                            if alreadyExist == False:
                                standards.add_standard(createStandard(supportedStandardRef, standardRef))
                                supportedStandardCreated=True

    supportedStandardFound = False
    for supportedStandard in supportedStandards.get_supportedStandard():
        if supportedStandard.get_ref() == supportedStandardRef:
            supportedStandardFound = True

    if supportedStandardFound == False and supportedStandardCreated == True:
        supportedStandards.add_supportedStandard(sl.supportedStandardType.factory(ref=supportedStandardRef,name=supportedStandard_name))
        rootObj.set_revision(int(rootObj.get_revision())+1)
        output_path=Path.cwd() / "outFiles" / "libraries" / library_path.name
        exportLib2XML(str(output_path), rootObj)
        text="SuportedStandard was added for the library and saved in the new created file '%s'\n"%output_path

    else:
        if supportedStandardCreated == True:
            rootObj.set_revision(int(rootObj.get_revision())+1)
            output_path=Path.cwd() / "outFiles" / "libraries" / library_path.name
            exportLib2XML(str(output_path), rootObj)
            text="SuportedStandard was updated for the library and saved in the new created file '%s'\n"%output_path
        else:
            text="SuportedStandard was not necessary to create for the library '%s'\n"%library_path.name

    print(text)
    return text


def getStandards(library_path, csvOut):

    if os.path.exists(library_path):
        root = etree.parse(str(library_path))
    else:
        return f"Problem found loading file: {library_path} (does it exists?)"

    df = pd.DataFrame(columns=["Component", "Control", "Supported Standard Name",
                               "Supported Standard Ref", "Standard Ref"])
    supportedStandards = dict()
    cont = 0

    # Create a supported standards dictionary
    for supStandard in root.iter('supportedStandard'):
        supportedStandards[supStandard.attrib['ref']] = supStandard.attrib['name']

    logger.info("Processing...")
    for component in root.iter('component'):
        for control in component.find('controls').iter('control'):
            for standard in control.find('standards').iter('standard'):
                # For every standard in a control we create a row with the dfm.columns data
                # df.loc[cont] sets content for a concrete index
                df.loc[cont] = [component.attrib['ref'], control.attrib['ref'],
                                supportedStandards[standard.attrib['supportedStandardRef']],
                                standard.attrib['supportedStandardRef'], standard.attrib['ref']]
                cont += 1

    df.to_csv(path_or_buf=csvOut, sep=",", index=False, line_terminator="\n")

    result = f"Standards for {library_path} correctly exported to {csvOut}"
    logger.info(result)

    return result


def setStandard(standard_file_path, library_path, out_library_path, action_a):

    root = etree.parse(str(library_path), etree.XMLParser(remove_blank_text=True))
    modified = False
    supportedStandardsToRemove = set()

    # Read CSV file
    dfm = pd.read_csv(str(standard_file_path), sep=",")
    dfm.columns = ["Component", "Control", "Supported Standard Name", "Supported Standard Ref", "Standard Ref"]

    # Get supported standards refs
    supportedStandardsRef = [supportedStandard.attrib['ref']
                             for supportedStandard in list(root.iter('supportedStandard'))]

    for index, row in dfm.iterrows():
        component_ref = row.get("Component")
        control_ref = str(row.get("Control"))
        supportedStandard_name = row.get("Supported Standard Name")
        supportedStandard_ref = row.get("Supported Standard Ref")
        standard_ref = row.get("Standard Ref")

        for component in root.find('components').iter('component'):
            if component.attrib['ref'] == component_ref:
                for control in component.find('controls').iter('control'):
                    if control.attrib['ref'] == control_ref:
                        if action_a == "add":
                            # If we want to add standards
                            # Get standards in control
                            standardsInControl = [std.attrib['supportedStandardRef'] + "-" + std.attrib['ref']
                                                  for std in list(control.find('standards').iter('standard'))]
                            if str(supportedStandard_ref) + "-" + str(standard_ref) not in standardsInControl:
                                # Add standard
                                new = etree.Element("standard")
                                new.attrib['ref'] = str(standard_ref)
                                new.attrib['supportedStandardRef'] = str(supportedStandard_ref)
                                control.find('standards').append(new)
                                logger.info(f"Standard {supportedStandard_ref}-{standard_ref} added to {control_ref} "
                                            f"in component {component_ref}")
                                modified = True

                                if supportedStandard_ref not in supportedStandardsRef:
                                    # Add supported standard
                                    new = etree.Element("supportedStandard")
                                    new.attrib['ref'] = supportedStandard_ref
                                    new.attrib['name'] = supportedStandard_name
                                    root.find('supportedStandards').append(new)
                                    supportedStandardsRef.append(supportedStandard_ref)

                        elif action_a == "delete":
                            # If we want to delete standards
                            # Get control standards elements
                            standards = list(control.find('standards').iter('standard'))
                            # Get standards ref to remove
                            toRemove = [x for x in standards
                                        if str(x.attrib['supportedStandardRef']) == str(supportedStandard_ref)
                                        and str(x.attrib['ref']) == str(standard_ref)]

                            # For every standard to remove in the control
                            for supportedStandardToRemove in toRemove:
                                # Add supported standard to remove list just in case we need to remove it
                                supportedStandardsToRemove.add(supportedStandardToRemove.attrib['supportedStandardRef'])
                                # Remove the standard from the control
                                control.find('standards').remove(supportedStandardToRemove)
                                logger.info(f"Removed {supportedStandard_ref}-{standard_ref} "
                                            f"from control {control_ref} in component {component_ref}")
                                modified = True
                        else:
                            pass

    if modified:
        # Remove supported standards if necessary
        if action_a == "delete" and not supportedStandardsToRemove:
            logger.info("No supported standards to remove")
        else:
            allSupportedStandardsUsed = set([std.attrib['supportedStandardRef'] for std in list(root.iter('standard'))])
            allSupportedStandardsDefined = list(root.iter('supportedStandard'))

            for supportedStandardToRemove in supportedStandardsToRemove:
                if supportedStandardToRemove not in allSupportedStandardsUsed:
                    for supStd in allSupportedStandardsDefined:
                        if supStd.attrib['ref'] == supportedStandardToRemove:
                            root.find('supportedStandards').remove(supStd)
                            logger.info(f"Deleted Supported Standard {supportedStandardToRemove}: not used anymore")

        root.getroot().attrib['revision'] = str(int(root.getroot().attrib['revision']) + 1)
        xmlFile = open(str(out_library_path), 'w', encoding="utf8")
        xmlFile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        xmlFile.write(etree.tostring(root, pretty_print=True).decode())
        xmlFile.close()

        convertCRLFtoLF(xmlFile.name)

        result = f"Library {out_library_path} modified"
    else:
        result = f"Library {out_library_path} not modified"

    logger.info(result)

    return result


def addXmlTag(pathFile):
    openFile=open(pathFile,'r')
    data=openFile.read()
    openFile.close()
    data="<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"+data
    output=open(pathFile,'w')
    output.write(data)
    output.close()

def addStandardToLibrary(standard_path_csv, path_library, standardName):
    path_xsd=Path.cwd() / "inputFiles" / "XSD_Schema" / "library.xsd"
    if xmlValidator(path_library, path_xsd) == True:
        return searchControls(path_library, standardName, standard_path_csv)

if __name__ == "__main__":
    csv = Path.cwd() / "inputFiles" / "standardsFiles" / "standardEditor.csv"
    library = Path.cwd() / "inputFiles" / "oldRelease" / "CS-Default.xml"
    libraryOut = Path.cwd() / "outFiles" / "outputLibs" / "CS-Default2.xml"
    action = "delete"
    #print(getStandards(library, csv))
    print(setStandard(csv, library, libraryOut, action))

