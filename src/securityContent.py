# -*- coding: utf-8 -*-
import sys
import math
import pandas as pd

class SecurityContent:
    def __init__(self, logger):
        #We declare a dictionary of lists to hold the security content
        self.content = {}
        self.logger = logger
     



    def importExcel(self, file_path):
        sheetName=""
        if not file_path.exists():
            print("File ", file_path, " doesn't exist!")
            sys.exit(1)
        else:
            xls = pd.ExcelFile(file_path)
            #We Read the first sheet of the workBook without using headers and skipping the first two rows.
            dataSet = pd.read_excel(xls, sheet_name='Risk Patterns', header=None, skiprows=2)
            if len(dataSet.values) > 0:
                #We have 20 columnns in the Excel
                dataSet.columns = ['componentId', 'componentName', 'componentDesc', 
                                    'usecaseId', 'usecaseName', 'usecaseDesc',
                                    'threatId', 'threatName', 'threatDesc', 'threatRefs',
                                    'weaknessId', 'weaknessName', 'weaknessDesc', 'weaknessRefs',
                                    'controlId', 'controlName', 'controlDesc', 'controlTestSteps', 'controlRefs', 'controlStandards']

                excelColumnsWithMergedCells = ['componentId', 'componentName', 'componentDesc', 
                                            'usecaseId', 'usecaseName', 'usecaseDesc',
                                            'threatId', 'threatName', 'threatDesc', 'threatRefs',
                                            'weaknessId', 'weaknessName', 'weaknessDesc', 'weaknessRefs']

                dataSet.update(dataSet[excelColumnsWithMergedCells].fillna(method='ffill'))
                #The rest of NaN cells are legitimate empty columns (Not merged cells like before) so we change NaN to an empty string to avoid problems in later processing
                dataSet.update(dataSet.fillna(""))

                #print(dataSet[['componentId', 'usecase', 'threatId', 'threatRefs', 'weaknessId', 'weaknessRefs', 'controlId', 'controlTestSteps']])
                #print('Data set size: ', dataSet.shape)

                #We fill the dictionary of list for Security Control with the Pandas Dataframe Object
                self.content = dataSet.to_dict(orient='list')

                self.logger.info("Excel importation process: OK")

    def setEmptySecurityContent(self):
        self.content = {}
        self.logger.info("Setting empty security content")

    def getUsecasesFromComponentId(self, componentId):
        componentIds = self.content['componentId']
        usecases = self.content['usecaseId']
        selUsecases = []

        for (c, u) in zip(componentIds, usecases):
            if (c==componentId):
                selUsecases.append(u)

        return self.removeDuplicates(selUsecases)

    def getThreatIdsFromComponentId(self, componentId):
        componentIds = self.content['componentId']
        threatIds = self.content['threatId']
        selThreatIds = []

        for (c, u) in zip(componentIds, threatIds):
            if (c==componentId):
                selThreatIds.append(u)

        return self.removeDuplicates(selThreatIds)

    def getNumberOfComponents(self):
        return len(self.removeDuplicates(self.content['componentId']))

    def getComponentIds(self):
        if len(self.content) != 0:
            return self.removeDuplicates(self.content['componentId'])
        return self.content

    def getComponentNames(self):
        if len(self.content) != 0:
            return self.removeDuplicates(self.content['componentName'])
        else:
            return self.content

    def getWeaknessIdsFromComponentId(self, componentId):
        componentIds = self.content['componentId']
        weaknessIds = self.content['weaknessId']
        selWeaknessIds = []

        for (c, w) in zip(componentIds, weaknessIds):
            if (c==componentId):
                selWeaknessIds.append(w)

        #We remove duplicates
        return self.removeDuplicates(selWeaknessIds)

    def getWeaknessNamesFromComponentId(self, componentId):
        selWeaknessIds = self.getWeaknessIdsFromComponentId(componentId)
        selWeaknessNames = []

        for w in selWeaknessIds:
            selWeaknessNames.append(self.getWeaknessNameFromWeaknessId(w))

        return selWeaknessNames

    def getWeaknessDescsFromComponentId(self, componentId):
        selWeaknessIds = self.getWeaknessIdsFromComponentId(componentId)
        selWeaknessDescs = []

        for w in selWeaknessIds:
            selWeaknessDescs.append(self.getWeaknessDescFromWeaknessId(w))

        return selWeaknessDescs

    def removeDuplicates(self, listOfvalues):
        seen = set() #We use set to remove duplicates in the list but preserving order
        return [x for x in listOfvalues if not (x in seen or seen.add(x))]

    def getWeaknessNameFromWeaknessId(self, weaknessId):
        weaknessIds = self.content['weaknessId']
        index = weaknessIds.index(weaknessId)
        return self.content['weaknessName'][index]

    def getWeaknessDescFromWeaknessId(self, weaknessId):
        weaknessIds = self.content['weaknessId']
        index = weaknessIds.index(weaknessId)
        return self.content['weaknessDesc'][index]

    def getControlIdsFromComponentId(self, componentId):
        componentIds = self.content['componentId']
        controlIds = self.content['controlId']
        selControlIds = []

        for (c, con) in zip(componentIds, controlIds):
            if (c==componentId):
                selControlIds.append(con)

        #We remove duplicates
        return self.removeDuplicates(selControlIds)

    def getControlNamesFromComponentId(self, componentId):
        selControlIds = self.getControlIdsFromComponentId(componentId)
        selControlNames = []

        for con in selControlIds:
            selControlNames.append(self.getControlNameFromControlId(con))

        return selControlNames

    def getControlNameFromControlId(self, controlId):
        controlIds = self.content['controlId']
        index = controlIds.index(controlId)
        return self.content['controlName'][index]
        
    def getControlDescsFromComponentId(self, componentId):
        selControlIds = self.getControlIdsFromComponentId(componentId)
        selControlDescs = []

        for con in selControlIds:
            selControlDescs.append(self.getControlDescFromControlId(con))

        return selControlDescs

    def getControlDescFromControlId(self, controlId):
        controlIds = self.content['controlId']
        index = controlIds.index(controlId)
        return self.content['controlDesc'][index]

    def getControlTestsStepsFromComponentId(self, componentId):
        selControlIds = self.getControlIdsFromComponentId(componentId)
        selControlTestSteps = []

        for con in selControlIds:
            selControlTestSteps.append(self.getControlTestStepsFromControlId(con))

        return selControlTestSteps

    def getControlTestStepsFromControlId(self, controlId):
        controlIds = self.content['controlId']
        index = controlIds.index(controlId)
        return self.content['controlTestSteps'][index]

    def getControlReferencesFromComponentId(self, componentId):
        selControlIds = self.getControlIdsFromComponentId(componentId)
        selControlReferences = []

        for con in selControlIds:
            selControlReferences.append(self.getControlReferencesFromControlId(con))

        return selControlReferences

    def getControlReferencesFromControlId(self, controlId):
        controlIds = self.content['controlId']
        index = controlIds.index(controlId)
        return self.content['controlRefs'][index]

    def getControlStandardsFromControlId(self, controlId):
        controlIds = self.content['controlId']
        index = controlIds.index(controlId)
        return self.content['controlStandards'][index]

    def getControlStandardsFromComponentId(self, componentId):
        selControlIds = self.getControlIdsFromComponentId(componentId)
        selControlStandards = []
        for con in selControlIds:
            selControlStandards.append(self.getControlStandardsFromControlId(con))

        return selControlStandards

    def getUseCaseIdsFromComponentId(self, componentId):
        componentIds = self.content['componentId']
        useCaseRefs = self.content['usecaseId']
        selUseCaseRefs = []

        for (c, ucref) in zip(componentIds, useCaseRefs):
            if (c == componentId):
                selUseCaseRefs.append(ucref)

        # We remove duplicates
        return self.removeDuplicates(selUseCaseRefs)

    def getUseCaseNamesFromComponentId(self, componentId):
        componentIds = self.content['componentId']
        useCaseNames = self.content['usecaseName']
        selUseCaseNames = []

        for (c, ucname) in zip(componentIds, useCaseNames):
            if (c == componentId):
                selUseCaseNames.append(ucname)

        # We remove duplicates
        return self.removeDuplicates(selUseCaseNames)

    def getUseCaseDescsFromComponentId(self, componentId):
        componentIds = self.content['componentId']
        useCaseIds = self.content['usecaseId']
        selUseCaseDescs = []
        already = []
        for (c, uc) in zip(componentIds, useCaseIds):
            if (c == componentId and uc not in already):
                already.append(uc)
                selUseCaseDescs.append("")

        # We remove duplicates
        return selUseCaseDescs

    def getThreatIdsFromComponentIdAndUseCase(self,componentId, usecase):
        componentIds = self.content['componentId']
        useCaseNames = self.content['usecaseId']
        threatIds = self.content['threatId']
        selThreatIds = []

        for (c, ucname, threatId) in zip(componentIds, useCaseNames, threatIds):
            if (c==componentId) and (ucname==usecase):
                selThreatIds.append(threatId)

        #We remove duplicates
        return self.removeDuplicates(selThreatIds)

    def getThreatNameFromThreatId(self, threatId):
        threatIds = self.content['threatId']
        index = threatIds.index(threatId)
        return self.content['threatName'][index]

    def getThreatNamesFromComponentIdAndUseCase(self, componentId, usecase):
        selThreatlIds = self.getThreatIdsFromComponentIdAndUseCase(componentId, usecase)
        selThreatNames = []

        for threatId in selThreatlIds:
            selThreatNames.append(self.getThreatNameFromThreatId(threatId))

        return selThreatNames

    def getThreatDescFromThreatId(self, threatId):
        threatIds = self.content['threatId']
        index = threatIds.index(threatId)
        return self.content['threatDesc'][index]

    def getThreatDescsFromComponentIdAndUseCase(self, componentId, usecase):
        selThreatlIds = self.getThreatIdsFromComponentIdAndUseCase(componentId, usecase)
        selThreatDescs = []

        for threatId in selThreatlIds:
            selThreatDescs.append(self.getThreatDescFromThreatId(threatId))

        return selThreatDescs

    def getControlIdsFromThreatIdAndComponentId(self, threatId, componentId):
        threatIds = self.content['threatId']
        controlIds = self.content['controlId']
        componentIds = self.content['componentId']
        selControlIds = []

        for (t, con, com) in zip(threatIds, controlIds, componentIds):
            if (t==threatId) and (com==componentId):
                selControlIds.append(con)

        #We remove duplicates
        return self.removeDuplicates(selControlIds)

    def calculateControlsMitigations(self, controlRefs):
        mitigations = []
        if len(controlRefs) > 0:
            mitigationFactor = int(self.round_down(100/len(controlRefs)))
            mitigations = [mitigationFactor for j in range(len(controlRefs))]
            i = 0
            while sum(mitigations) < 100:
                mitigations[i] += 1
                i += 1 

            # using zip() to convert lists to dictionary 
            controlsDict = dict(zip(controlRefs, mitigations)) 

            return controlsDict
        else:
            self.logger.error("Error Calculating mitigation factor for controls: No controls for this threat") 

    def getFilteredControlsDictByControlRefs(self, controlsDict, controlRefs):
        #We get a dictionary from the master dictionary that have the key values in the list controlsRefs
        filteredControlsDict = { key:value for key,value in controlsDict.items() if key in controlRefs}

        return filteredControlsDict

    def getWeaknessIdsFromThreatIdAndComponentId(self, threatId, componentId):
        threatIds = self.content['threatId']
        weaknessIds = self.content['weaknessId']
        componentIds = self.content['componentId']
        selWeakneesIds = []

        for (t, w, com) in zip(threatIds, weaknessIds, componentIds):
            if (t==threatId) and (com==componentId):
                selWeakneesIds.append(w)

        #We remove duplicates
        return self.removeDuplicates(selWeakneesIds)

    def getControlIdsFromWeaknessIdAndThreatIdAndComponentId(self, weaknessId, threatId, componentId):
        weaknessIds = self.content['weaknessId']
        controlIds = self.content['controlId']
        threatIds = self.content['threatId']
        componentIds = self.content['componentId']

        selControlIds = []

        for (w, con, t, com) in zip(weaknessIds, controlIds, threatIds, componentIds):
            if (w==weaknessId) and (t==threatId) and (com==componentId):
                selControlIds.append(con)

        #We remove duplicates
        return self.removeDuplicates(selControlIds)

    def round_down(self, n):
        return math.floor(n)

    

