import logging
from lxml import etree
from src.convertCrlfToLf import convertCRLFtoLF

# Logger
logging.basicConfig(filename="logFile.log",
                    format='%(asctime)s  %(levelname)-10s %(message)s',
                    datefmt="%Y-%m-%d-%H-%M-%S",
                    filemode='w')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def createLibraryFromDefaultOne(baseLibrary, outPath, name, ref, userWantsASVS3):
    # First we create the new file by taking the base library and replacing the refs
    baseLibraryTree = etree.parse(str(baseLibrary))
    baseRef = baseLibraryTree.getroot().attrib['ref']

    fin = open(baseLibrary, "rt", encoding='utf-8')
    fout = open(outPath, "wt", encoding='utf-8')
    for line in fin:
        fout.write(line.replace(baseRef, ref))
    fin.close()
    fout.close()

    # Second we parse the new library to set the correct name and revision
    newCopyTree = etree.parse(str(outPath))
    root = newCopyTree.getroot()
    root.attrib['name'] = name
    root.attrib['revision'] = "1"

    asvsToRemove = "owasp-asvs-"
    asvsToNotRemove = "owasp-asvs4-"
    if userWantsASVS3:
        asvsToRemove = "owasp-asvs4-"
        asvsToNotRemove = "owasp-asvs-"

    for component in root.iter('component'):
        controlsToRemove = set()
        for control in component.find('controls').iter('control'):
            supStd = set([x.attrib['supportedStandardRef'].lower() for x in list(control.iter('standard'))])
            logger.info(component.attrib['ref'] + " : " + control.attrib['ref'] + " : " + str(supStd))

            # If there is a control with only one type of ASVS standard to remove it will be marked to deletion
            if any(map(lambda x: asvsToRemove in x, supStd)) and not any(map(lambda x: asvsToNotRemove in x, supStd)):
                controlsToRemove.add(control.attrib['ref'])

        if controlsToRemove:
            logger.info("Controls to remove: " + component.attrib['ref'] + " : " + str(controlsToRemove))
            for control in component.find('controls').iter('control'):
                if control.attrib['ref'] in controlsToRemove:
                    control.getparent().remove(control)
            for threat in component.iter('threat'):
                for control in threat.iter('control'):
                    if control.attrib['ref'] in controlsToRemove:
                        control.getparent().remove(control)

    for supportedStandard in root.iter('supportedStandard'):
        standardUsedInAnyComponent = False
        ref = supportedStandard.attrib['ref']
        for component in root.iter('component'):
            for control in component.find('controls').iter('control'):
                for standard in control.iter('standard'):
                    if standard.attrib['supportedStandardRef'] == ref:
                        standardUsedInAnyComponent = True

        if not standardUsedInAnyComponent:
            supportedStandard.getparent().remove(supportedStandard)
            logger.info("Removed supported standard " + ref)

    newCopyTree.write(str(outPath))

    # Finally we create the XML tag and remove any possible CRLF
    xmlFile = open(str(outPath), 'w', encoding="utf8")
    xmlFile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    xmlFile.write(etree.tostring(newCopyTree, pretty_print=True).decode())
    xmlFile.close()
    convertCRLFtoLF(xmlFile.name)

    return outPath


def main():
    createLibraryFromDefaultOne(
        "C:\\CS\\Workspace\\iriusrisktoolkitui\\libraries\\CS-Default.xml",
        "C:\\CS\\Workspace\\iriusrisktoolkitui\\outFiles\\libraries\\AlvaroReyes.xml",
        "Alvaro",
        "Reyes",
        False)


if __name__ == '__main__':
    main()
