from pathlib import Path
import logging
import os
import sys
from src.mitigationValidator import libMitigationTest


import src.sample_lib as supermod
import src.xmlValidator as xmlcheck

import src.securityContent as SecurityContent
from src.xmlValidator import xmlValidator

logging.basicConfig(filename="logFile.log",
                    format='%(asctime)s  %(levelname)-10s %(message)s',
                    datefmt="%Y-%m-%d-%H-%M-%S",
                    filemode='w')

# Creating an object
logger = logging.getLogger()

# Setting the threshold of logger to INFO
logger.setLevel(logging.INFO)

# We update the first use case with the data of the second use case


def setUseCaseDetails(firstUseCase, secondUseCase):
    logger.info("INFO: Use case with id '%s' was updated." %
                firstUseCase.get_ref())
    firstUseCase.set_name(secondUseCase.get_name())
    firstUseCase.set_desc(secondUseCase.get_desc())

    return firstUseCase
# We update the first component with the data of the second component


def setComponentDetails(firstComponent, secondComponent):
    logger.info("INFO: Component with id '%s' was updated." %
                firstComponent.get_ref())
    firstComponent.set_name(secondComponent.get_name())
    firstComponent.set_desc(secondComponent.get_desc())

    return firstComponent
# We update the first Category component with the data of the second Category component


def setCategoryComponentDetails(firstCategoryComponent, secondCategoryComponent):
    logger.info("INFO: Category Component with id '%s' was updated." %
                firstCategoryComponent.get_ref())
    firstCategoryComponent.set_name(secondCategoryComponent.get_name())

    return firstCategoryComponent
# We update the first Component Definition with the data of the second Component Definition


def setComponentDefinitionDetails(firstComponentDefinition, secondComponentDefinition):
    logger.info("INFO: Component Definition with id '%s' was updated." %
                firstComponentDefinition.get_ref())
    firstComponentDefinition.set_name(secondComponentDefinition.get_name())
    firstComponentDefinition.set_desc(secondComponentDefinition.get_desc())
    firstComponentDefinition.set_riskPatterns(
        secondComponentDefinition.get_riskPatterns())

    return firstComponentDefinition
# We update the first Supported Standard with the data of the second Supported Standard


def setSupportedStandardDetails(firstSS, secondSS):
    logger.info("INFO: Supported Standard with id '%s' was updated." %
                firstSS.get_ref())
    firstSS.set_name(secondSS.get_name())

    return firstSS
# We update the first threat with the data of the second threat


def setThreatDetails(firstThreat, secondThreat):
    logger.info("INFO: Threat with id '%s' was updated." %
                firstThreat.get_ref())
    firstThreat.set_name(secondThreat.get_name())
    firstThreat.set_desc(secondThreat.get_desc())
    firstThreat.set_riskRating(secondThreat.get_riskRating())
    firstThreat.set_references(secondThreat.get_references())
    firstThreat.set_state(secondThreat.get_state())
    firstThreat.set_source(secondThreat.get_source())
    firstThreat.set_owner(secondThreat.get_owner())
    firstThreat.set_library(secondThreat.get_library())

    return firstThreat
# We update the first weakness with the data of the second weakness


def setWeaknessDetails(firstWeakness, secondWeakness):
    logger.info("INFO: Weakness with id '%s' was updated." %
                firstWeakness.get_ref())
    firstWeakness.set_name(secondWeakness.get_name())
    firstWeakness.set_test(secondWeakness.get_test())
    firstWeakness.set_desc(secondWeakness.get_desc())
    firstWeakness.set_state(secondWeakness.get_state())
    firstWeakness.set_impact(secondWeakness.get_impact())
    firstWeakness.set_issueId(secondWeakness.get_issueId())

    return firstWeakness
# We update the first countermeasure with the data of the second countermeasure

def checkIfReferenceExistsInMaster(firstControl, secondControl):

    for reference in secondControl.get_references().get_reference():
        found=False
        for ref in firstControl.get_references().get_reference():
            if reference.get_name() == ref.get_name() and reference.get_url() == ref.get_url():
                found=True
        if not found:
            firstControl.get_references().add_reference(reference)
            logger.info("Reference '%s' was included into the countermeasure '%s'." % (
                reference.get_name(), firstControl.get_ref()))
    return firstControl

def checkIfStandardExistsInMaster(firstControl, secondControl):
    for standard in secondControl.get_standards().get_standard():
        found=False
        for s in firstControl.get_standards().get_standard():
            if standard.get_ref() == s.get_ref() and standard.get_supportedStandardRef() == s.get_supportedStandardRef():
                found=True

        if not found:
            firstControl.get_standards().add_standard(standard)
            logger.info("Standard '%s-%s' was included into the countermeasure '%s'." %
                        (standard.get_supportedStandardRef(), standard.get_ref(), firstControl.get_ref()))
    return firstControl

def setCountermeasureDetails(firstControl, secondControl):
    logger.info("INFO: Countermeasure with id '%s' was updated." %
                firstControl.get_ref())
    firstControl.set_name(secondControl.get_name())
    firstControl.set_desc(secondControl.get_desc())
    firstControl.set_implementations(secondControl.get_implementations())
    firstControl = checkIfReferenceExistsInMaster(firstControl, secondControl)
    firstControl = checkIfStandardExistsInMaster(firstControl, secondControl)
    firstControl.set_udts(secondControl.get_udts())
    firstControl.set_test(secondControl.get_test())
    firstControl.set_issueId(secondControl.get_issueId())
    firstControl.set_platform(secondControl.get_platform())
    firstControl.set_cost(secondControl.get_cost())
    firstControl.set_risk(secondControl.get_risk())
    firstControl.set_state(secondControl.get_state())
    firstControl.set_owner(secondControl.get_owner())
    firstControl.set_library(secondControl.get_library())
    firstControl.set_source(secondControl.get_source())

    return firstControl
# We check the differencies between both libraries, if the category component doesn't exist, we include it, but if it exists, we update it in the primary library.


def checkCategoryComponent(firstCategoryComponents, secondCategoryComponents):
    for secondCategoryComponent in secondCategoryComponents.get_categoryComponent():
        categoryFound = False
        for firstCategoryComponent in firstCategoryComponents.get_categoryComponent():
            if secondCategoryComponent.get_ref() == firstCategoryComponent.get_ref():
                categoryFound = True
                firstCategoryComponent = setCategoryComponentDetails(
                    firstCategoryComponent, secondCategoryComponent)
        if categoryFound == False:
            firstCategoryComponents.add_categoryComponent(secondCategoryComponent)
            logger.info("INFO: Risk Pattern '%s' was mapped." %
                        secondCategoryComponent.get_ref())
# We check the differencies between both libraries, if the risk pattern doesn't exist, we include it, but if it exists, we update it in the primary library.


def checkRiskPatterns(firstRiskPatterns, secondRiskPatterns):
    for secondRiskPattern in secondRiskPatterns.get_riskPattern():
        riskPatternFound = False
        for firstRiskPattern in firstRiskPatterns.get_riskPattern():
            if secondRiskPattern.get_ref() == firstRiskPattern.get_ref():
                riskPatternFound = True
        if riskPatternFound == False:
            firstRiskPatterns.add_riskPattern(secondRiskPattern)
            logger.info("INFO: Risk Pattern '%s' was mapped." %
                        secondRiskPattern.get_ref())
# We check the differencies between both libraries, if the component definition doesn't exist, we include it, but if it exists, we update it in the primary library.


def checkComponentDefinitions(firstCompDefs, secondCompDefs):
    for secondCompDef in secondCompDefs.get_componentDefinition():
        compDefFound = False
        for firstCompDef in firstCompDefs.get_componentDefinition():
            if secondCompDef.get_ref() == firstCompDef.get_ref():
                compDefFound = True
                firstCompDef = setComponentDefinitionDetails(
                    firstCompDef, secondCompDef)
                firstRiskPatterns = firstCompDef.get_riskPatterns()
                secondRiskPatterns = secondCompDef.get_riskPatterns()
                checkRiskPatterns(firstRiskPatterns, secondRiskPatterns)
        if compDefFound == False:
            firstCompDefs.add_componentDefinition(secondCompDef)
            logger.info("INFO: Component Definition '%s' was added." %
                        secondCompDef.get_ref())
# We check the differencies between both libraries, if the weakness is not mapped to the corresponding threat, we map it.


def checkMappingControls(firstControls, secondControls):
    for secondControl in secondControls.get_control():
        controlFound = False
        for firstControl in firstControls.get_control():
            if secondControl.get_ref() == firstControl.get_ref():
                controlFound = True
        if controlFound == False:
            firstControls.add_control(secondControl)
            logger.info("INFO: Control '%s' was mapped." %
                        secondControl.get_ref())

# We check the differencies between both libraries, if the weakness is not mapped to the corresponding threat, we map it, but if it is mapped, we update their countermeasures.


def checkMappingWeaknesses(firstWeaknesses, secondWeaknesses):
    for secondWeakness in secondWeaknesses.get_weakness():
        weaknessFound = False
        for firstWeakness in firstWeaknesses.get_weakness():
            if secondWeakness.get_ref() == firstWeakness.get_ref():
                weaknessFound = True
                firstControls = firstWeakness.get_controls()
                secondControls = secondWeakness.get_controls()
                checkMappingControls(firstControls, secondControls)
        if weaknessFound == False:
            firstWeaknesses.add_weakness(secondWeakness)
            logger.info("INFO: Weakness '%s' was mapped." %
                        secondWeakness.get_ref())

# We check the differencies between both libraries, if the threat doesn't exist, we include it, but if it exists, we update it in the primary library.


def checkThreats(firstThreats, secondThreats):
    for secondThreat in secondThreats.get_threat():
        threatFound = False
        for firstThreat in firstThreats.get_threat():
            if secondThreat.get_ref() == firstThreat.get_ref():
                firstThreat = setThreatDetails(firstThreat, secondThreat)
                threatFound = True
                firstWeaknesses = firstThreat.get_weaknesses()
                secondWeaknesses = secondThreat.get_weaknesses()
                checkMappingWeaknesses(firstWeaknesses, secondWeaknesses)

                firstControls = firstThreat.get_controls()
                secondControls = secondThreat.get_controls()
                checkMappingControls(firstControls, secondControls)

        if threatFound == False:
            firstThreats.add_threat(secondThreat)
            logger.info("INFO: Threat '%s' was added." %
                        secondThreat.get_ref())

# We check the differencies between both libraries, if the use case doesn't exist, we include it, but if it exists, we update it in the primary library.


def checkUsecases(firstUsecases, secondUsecases):
    for secondUsecase in secondUsecases.get_usecase():
        usecaseFound = False
        for firstUsecase in firstUsecases.get_usecase():
            if secondUsecase.get_ref() == firstUsecase.get_ref():
                usecaseFound = True
                firstUsecase = setUseCaseDetails(firstUsecase, secondUsecase)
                firstThreats = firstUsecase.get_threats()
                secondThreats = secondUsecase.get_threats()
                checkThreats(firstThreats, secondThreats)
                logger.info("Threats: MERGED")
        if usecaseFound == False:
            firstUsecases.add_usecase(secondUsecase)
            logger.info("INFO: Use case '%s' was added." %
                        secondUsecase.get_ref())
# We check the differencies between both libraries, if the weakness doesn't exist, we include it, but if it exists, we update it in the primary library.


def checkWeaknesses(firstWeaknesses, secondWeaknesses):
    for secondWeakness in secondWeaknesses.get_weakness():
        weaknessFound = False
        for firstWeakness in firstWeaknesses.get_weakness():
            if secondWeakness.get_ref() == firstWeakness.get_ref():
                weaknessFound = True
                firstWeakness = setWeaknessDetails(
                    firstWeakness, secondWeakness)
        if weaknessFound == False:
            firstWeaknesses.add_weakness(secondWeakness)
            logger.info("INFO: Weakness '%s' was added." %
                        secondWeakness.get_ref())
# We check the differencies between both libraries, if the countermeasure doesn't exist, we include it, but if it exists, we update it in the primary library.


def checkCountermeasures(firstControls, secondControls):
    for secondControl in secondControls.get_control():
        controlFound = False
        for firstControl in firstControls.get_control():
            if secondControl.get_ref() == firstControl.get_ref():
                controlFound = True
                firstControl = setCountermeasureDetails(
                    firstControl, secondControl)
        if controlFound == False:
            firstControls.add_control(secondControl)
            logger.info("INFO: Countermeasure '%s' was added." %
                        secondControl.get_ref())
# We check the differencies between both libraries, if the component doesn't exist, we include it, but if it exists, we update it in the primary library.


def checkComponents(firstComponents, secondComponents):
    for secondComponent in secondComponents.get_component():
        componentFound = False
        for firstComponent in firstComponents.get_component():
            if secondComponent.get_ref() == firstComponent.get_ref():
                componentFound = True
                firstComponent = setComponentDetails(
                    firstComponent, secondComponent)
                firstUsecases = firstComponent.get_usecases()
                secondUsecases = secondComponent.get_usecases()
                checkUsecases(firstUsecases, secondUsecases)

                firstControls = firstComponent.get_controls()
                secondControls = secondComponent.get_controls()
                checkCountermeasures(firstControls, secondControls)

                firstWeaknesses = firstComponent.get_weaknesses()
                secondWeaknesses = secondComponent.get_weaknesses()
                checkWeaknesses(firstWeaknesses, secondWeaknesses)
        if componentFound == False:
            firstComponents.add_component(secondComponent)
            logger.info("INFO: Component '%s' was added." %
                        secondComponent.get_ref())
# We check the differencies between both libraries, if the rule doesn't exist, we include it, but if it exists, we update it in the primary library.


def checkRules(firstRules, secondRules):
    for secondRule in secondRules.get_rule():
        ruleFound = False
        for firstRule in firstRules.get_rule():
            if secondRule.get_name() == firstRule.get_name():
                ruleFound = True
        if ruleFound == False:
            firstRules.add_rule(secondRule)
            logger.info("INFO: Rule '%s' was added." % secondRule.get_name())
# We check the differencies between both libraries, if the supported standard doesn't exist, we include it, but if it exists, we update it in the primary library.


def checkSupportedStandards(firstSupportedStandards, secondSupportedStandards):
    for secondSupportedStandard in secondSupportedStandards.get_supportedStandard():
        supportedStandardFound = False
        for firstSupportedStandard in firstSupportedStandards.get_supportedStandard():
            if secondSupportedStandard.get_ref() == firstSupportedStandard.get_ref():
                if secondSupportedStandard.get_name() != firstSupportedStandard.get_name():
                    firstSupportedStandard = setSupportedStandardDetails(
                        firstSupportedStandard, secondSupportedStandard)
                supportedStandardFound = True
        if supportedStandardFound == False:
            firstSupportedStandards.add_supportedStandard(
                secondSupportedStandard)
            logger.info("INFO: Supported Standardard '%s' was added." %
                        secondSupportedStandard.get_ref())


# We check the differencies between both libraries for each node (category components, component definitions, supported standards, risk patterns, rules)
def mergeLibraries(rootFirst, rootSecond):
    logger.info("INFO: Category Components to merge: STARTED")
    firstCategoryComponents = rootFirst.get_categoryComponents()
    secondCategoryComponents = rootSecond.get_categoryComponents()
    checkCategoryComponent(firstCategoryComponents, secondCategoryComponents)
    logger.info("INFO: Category Components to merge: FINISHED")

    logger.info("INFO: Supported Standard to merge: STARTED")
    firstSupportedStandard = rootFirst.get_supportedStandards()
    secondSupportedStandard = rootSecond.get_supportedStandards()
    checkSupportedStandards(firstSupportedStandard, secondSupportedStandard)
    logger.info("INFO: Supported Standard to merge: FINISHED")

    logger.info("INFO: Component Definitions to merge: STARTED")
    firstCompDefs = rootFirst.get_componentDefinitions()
    secondCompDefs = rootSecond.get_componentDefinitions()
    checkComponentDefinitions(firstCompDefs, secondCompDefs)
    logger.info("INFO: Component Definitions to merge: FINISHED")

    logger.info("INFO: Components to merge: STARTED")
    firstComponents = rootFirst.get_components()
    secondComponents = rootSecond.get_components()
    checkComponents(firstComponents, secondComponents)
    logger.info("INFO: Components to merge: FINISHED")

    logger.info("INFO: Rules to merge: STARTED")
    firstRules = rootFirst.get_rules()
    secondRules = rootSecond.get_rules()
    checkRules(firstRules, secondRules)
    logger.info("INFO: Rules to merge: FINISHED")


def removeContentFromRules(rootObj):
    for rule in rootObj.get_rules().get_rule():
        rule.set_content("")
    return rootObj

# We generate the file with the data of both libraries


def exportLib2XML(xmlFileName, rootObj):
    # We open the xml file and add the first lines of the project
    try:
        os.stat(os.path.dirname(xmlFileName))
    except:
        os.mkdir(os.path.dirname(xmlFileName))
    rootObj.set_revision(rootObj.get_revision()+1)
    rootObj = removeContentFromRules(rootObj)
    xmlFile = open(xmlFileName, 'w', encoding="utf8")
    xmlFile.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    rootTag = 'project'
    rootObj.export(xmlFile, 0, name_=rootTag,
                   namespacedef_='', pretty_print=True)
    print('Generated XML file -> ' + xmlFileName)
    logger.info('INFO: Generated XML file -> ' + xmlFileName)
# With this function, we generate the questions to select the libraries to merge.


def selectlibraryFromPath(path, mainText):
    try:
        os.stat(str(path))
    except:
        os.mkdir(str(path))
    libs=list()
    libraries = os.listdir(str(path))
    for lib in libraries:
        if lib.endswith(".xml"):
            libs.append(lib)
    if len(libs) == 0:
        print("There are not any library to use in the path '%s'.\nPlease provide the libraries to the path and rerun the script." % path)
        sys.exit(1)
    else:
        text = mainText+"\n"
        for lib in libs:
            text += "%i - %s \n" % (libs.index(lib), lib)
        inputFirst = input(text)
        return str(path / libraries[int(inputFirst)])

# In this function, we call the function to merge the libraries and it calls the functions to verify the generated xml file


def mergeLibrariesByPaths(pathFirstLibary, pathSecondLibrary):
    rootFirst = supermod.libraryType()
    rootFirst = supermod.parse(str(pathFirstLibary), True)
    rootSecond = supermod.libraryType()
    rootSecond = supermod.parse(str(pathSecondLibrary), True)
    logger.info("Merging two libraries process: STARTED")
    mergeLibraries(rootFirst, rootSecond)
    logger.info("Merging two libraries process: FINISHED")
    xmlFileName = str(Path.cwd() / "outFiles" / "mergedLibs" / pathFirstLibary.name)
    exportLib2XML(xmlFileName, rootFirst)
    xsd = str(Path.cwd() / "inputFiles" / "XSD_Schema" / "library.xsd")
    logger.info("XSD Validation of XML processes: STARTED")
    if xmlValidator(xmlFileName, xsd):
        print("XSD Schema validation: Success")
        logger.info(
            "XSD Validation of XML processes: FINISHED - with result: SUCCESS")
    else:
        print("XSD Schema validation: Failed")
        logger.error(
            "ERROR: XSD Validation of XML processes: FINISHED - with result: FAILED")
    logger.info("% Threat mitigation validation process: STARTED")
    print("\nTesting of Threat mitigations:\n")
    libMitigationTest(xmlFileName,[])
    logger.info("% Threat mitigation validation process: FINISHED")
    return "The last version (merged) of the library is located in the path %s.\n"%xmlFileName
# We run the main function of this file


def main():

    libFirst = selectlibraryFromPath(
        Path.cwd() / "libraries", "Select the number of the main library to use as base for the merging libraries process:")
    libSecond = selectlibraryFromPath(
        Path.cwd() / "inputFiles" / "libsToMerge", "Select the number of the second library to merge with the before library:")
    mergeLibrariesByPaths(libFirst, libSecond)


if __name__ == '__main__':
    main()
