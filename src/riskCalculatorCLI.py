#!/usr/bin/python
import sys
import xml.etree.ElementTree as ET
import argparse
from math import sqrt, ceil, floor

############### Script configuration ###############

businessImpactWeighting=8
assetValueWeighting=1
exposureWeighting=1
easeOfExploitationWeighting=1
mitigationFactorIfControlTestPassed=1
mitigationFactorIfControlTestNotPassed=1
mitigationFactorIfControlImplemented=1
vulnerabilityFoundFactor=0
trustZones={'Internet':1,'Public':1,'Public Cloud':60,'Trusted Partner':80,'Private Secured':100}

####################################################

# Return CIA Value for asset 
def getCIAValueForAsset(asset, cia, rootAssets):
	for a in rootAssets:
		if a.attrib['name'] == asset:
			classification = a.find('classification')
			return int(classification.attrib[cia])

# Normalize a value given a denominator
def normalize(value, denominator):
	return floor(value / denominator)

# Return mitigation factor (1) if test passed or test isn't failed and control is implemented
def getFactorCR(control, rootControl):
	ref = control.attrib['ref']
	for c in rootControl:
		if c.attrib['ref'] == ref:
			state = c.attrib['state']
			testResult = list(c.iter('source'))[0].attrib['result'] 
			print(f'	Control {ref} has state {state} and test {testResult}')

			if testResult == 'Passed':
				return mitigationFactorIfControlTestPassed
			elif testResult != 'Failed' and state == 'Implemented':
				return mitigationFactorIfControlImplemented
			else:
				return 0
			
	return 0

# Return mitigation factor (1) if control is Required or Implemented
def getFactorPR(control, rootControl):
	ref = control.attrib['ref']
	for c in rootControl:
		if c.attrib['ref'] == ref:
			state = c.attrib['state']
			print(f'	Control {ref} has state {state}')
			if state not in ['Required','Implemented']:
				return 0
			else:
				return mitigationFactorIfControlTestPassed
			
	return 0

# Returns a dictionary with 'C','I','A' and 'EE' entries which represent threat risk rating
def getThreatRiskRating(threat):
	componentThreatRiskRating = list(threat.iter('riskRating'))[0]
	componentThreatProps = {
		'C':int(componentThreatRiskRating.attrib['confidentiality']),
		'I':int(componentThreatRiskRating.attrib['integrity']),
		'A':int(componentThreatRiskRating.attrib['availability']),
		'EE':int(componentThreatRiskRating.attrib['easeOfExploitation'])
	}
	return componentThreatProps	

# Returns a dictionary with 'trustzone' and 'rating' entries which represent the trustzone of the component
def getComponentTrustZone(component):
	componentTrustZone = component.find('trustZones').find('trustZone').attrib['name']
	componentTz = {}
	if componentTrustZone in trustZones.keys():
		componentTz['trustzone']=componentTrustZone
		componentTz['rating']=trustZones[componentTrustZone]
	return componentTz

# Returns the maximum weakness impact
def getMaxWeaknessImpact(componentWeaknessFromComponentRoot, componentWeaknessFromComponentThreat):
	impacts = []
	for weakness in componentWeaknessFromComponentThreat:
		ref = weakness.attrib['ref']
		for w in componentWeaknessFromComponentRoot:
			if(w.attrib['ref'] == ref):
				impacts.append(int(w.attrib['impact']))			
	if len(impacts) == 0:
		return 100
	else:
		return max(impacts)

# Returns the maximum failed weakness impact
def getMaxFailedWeaknessImpact(componentWeaknessFromComponentRoot, componentWeaknessFromComponentThreat):
	impacts = []
	for weakness in componentWeaknessFromComponentThreat:
		ref = weakness.attrib['ref']
		for w in componentWeaknessFromComponentRoot:
			testResult = w.find('test').find('source').attrib['result']
			if(w.attrib['ref'] == ref and testResult == 'Failed'):
				impacts.append(int(w.attrib['impact']))			
	if len(impacts) == 0:
		return 100
	else:
		return max(impacts)

# Return the maximum average asset value
def getMaxAverageAssetValue(assets, rootAssets):
	# If there are no assets we return a default of 50
	if len(assets) == 0:
		return 50

	maxAvgCIA = 0
	for asset in rootAssets:
		if asset.attrib['name'] in assets:
			classification = asset.find('classification')

			confidentiality = int(classification.attrib['confidentiality'])
			integrity = int(classification.attrib['integrity'])
			availability = int(classification.attrib['availability'])

			avgCIA = round(sum([confidentiality, integrity, availability]) / 3)
			if avgCIA > maxAvgCIA:
				maxAvgCIA = avgCIA
	return maxAvgCIA

# Returns an asset name list for the component
def getComponentAssets(component):
	assets = []
	for asset in component.iter('asset'):
		assets.append(asset.attrib['name'])
	return assets

def color(word, color):
	
	CEND = '\033[0m'
	BGRED = '\033[41m'
	BGGREEN = '\033[42m'
	LIGHT_RED = "\033[1;31m"
	LIGHT_GREEN = "\033[1;32m"
	LIGHT_PURPLE = "\033[1;35m"
	CGREEN = '\033[32m'
	CYELLOW = '\033[33m'
	CBLUE = '\033[34m'
	CPINK = '\033[35m'
	CLBLUE = '\033[36m'
	switcher = {

		"lred": LIGHT_RED + word + CEND,
		"lgreen": LIGHT_GREEN + word + CEND,
		"lpink": LIGHT_PURPLE + word + CEND,
		"green": CGREEN + word + CEND,
		"bggreen": BGGREEN + word + CEND,
		"bgred": BGRED + word + CEND,
		"yellow": CYELLOW + word + CEND,
		"blue": CBLUE + word + CEND,
		"pink": CPINK + word + CEND,
		"lblue": CLBLUE + word + CEND
	}
	if color in switcher.keys():
		return switcher[color]
	else:
		return word

def calculateRisk(argv):
	tree = ET.parse(argv[1])
	root = tree.getroot()

	# First step: extract data for later use
	inherentRiskList = []
	currentRiskList = []
	projectedRiskList = []
	threatCount = 0
	businessImpactDenominator = businessImpactWeighting + assetValueWeighting
	probabilityDenominator = exposureWeighting + easeOfExploitationWeighting
	rootAssets = list(root.find('assets').iter('asset'))
	print()

	# For every component we need to calculate the risks for every threat in it
	# We prepare the assets and trustzone for the component
	for component in root.iter('component'):
		print("###################################################")
		print("### Component " + color(component.attrib['name'],"bggreen"))
		print("###################################################")

		# TrustZone 
		componentTz = getComponentTrustZone(component)
		
		# Assets (asset name list)
		componentAssets = getComponentAssets(component)
		
		# Weaknesses
		componentWeaknessFromComponentRoot = list(component.find('weaknesses').iter('weakness')) # Information

		# Second step: calculate the three types of risks for every threat
		
		# Calculate the maximum average asset value for this component
		maxAvgAssetValue = getMaxAverageAssetValue(componentAssets, rootAssets)

		# For every threat in component we calculate the risks
		for threat in component.iter('threat'): 
			threatCount += 1
			print(f'Threat: {color(threat.attrib["ref"],"bgred")} - {threat.attrib["name"]}')

			# Calculate the maximum weakness impact for this threat
			componentWeaknessFromComponentThreat = list(threat.find('weaknesses').iter('weakness')) # References
			greatestWeaknessImpact = getMaxWeaknessImpact(componentWeaknessFromComponentRoot, componentWeaknessFromComponentThreat)
			greatestFailedWeaknessImpact = getMaxFailedWeaknessImpact(componentWeaknessFromComponentRoot, componentWeaknessFromComponentThreat)

			# ####### Inherent Risk #######
			print(" + Calculating Inherent Risk...")
			print(f'	MaxWeaknessImpact: {color(str(greatestWeaknessImpact),"pink")}')
			print(f'	MaxFailedWeaknessImpact: {str(greatestFailedWeaknessImpact)}')
			print(f'	MaxAverageAssetValue: {color(str(maxAvgAssetValue),"lred")}')
			print(f'	businessImpactDenominator: {businessImpactDenominator}')
			print(f'	probabilityDenominator: {probabilityDenominator}')
			print(f'	TrustZone: {componentTz["trustzone"]} -> Rating: {componentTz["rating"]}')
			# Extract threat risk rating
			componentThreatProps = getThreatRiskRating(threat)
			print(f'	Threat CIA & EE: C={color(str(componentThreatProps["C"]),"green")} I={color(str(componentThreatProps["I"]),"yellow")} A={color(str(componentThreatProps["A"]),"blue")} EE={color(str(componentThreatProps["EE"]),"lblue")}')
			print()

			# Calculate impact: first we neet to calculate which asset has the greatest business impact
			greatestBusinessImpact=0
			if len(componentAssets)==0:
				C = 50
				I = 50
				A = 50

				confidencialityBusinessImpact	 = businessImpactWeighting * (componentThreatProps['C'] * greatestWeaknessImpact) / 100 + assetValueWeighting * C
				integrityBusinessImpact 		 = businessImpactWeighting * (componentThreatProps['I'] * greatestWeaknessImpact) / 100 + assetValueWeighting * I
				availabilityBusinessImpact 		 = businessImpactWeighting * (componentThreatProps['A'] * greatestWeaknessImpact) / 100 + assetValueWeighting * A
				print(f'	Asset: Default: C={color(str(C),"green")} I={color(str(I),"yellow")} A={color(str(A),"blue")}')
				print(f'	C = {businessImpactWeighting} * ({color(str(componentThreatProps["C"]),"green")} * {color(str(greatestWeaknessImpact),"pink")}) / 100 + {assetValueWeighting} * {color(str(C),"green")} = {confidencialityBusinessImpact}')
				print(f'	I = {businessImpactWeighting} * ({color(str(componentThreatProps["I"]),"yellow")} * {color(str(greatestWeaknessImpact),"pink")}) / 100 + {assetValueWeighting} * {color(str(I),"yellow")} = {integrityBusinessImpact}')
				print(f'	A = {businessImpactWeighting} * ({color(str(componentThreatProps["A"]),"blue")} * {color(str(greatestWeaknessImpact),"pink")}) / 100 + {assetValueWeighting} * {color(str(A),"blue")} = {availabilityBusinessImpact}')
				# We get the maximum value from CIA impact values
				greatestBusinessImpact = max(confidencialityBusinessImpact, integrityBusinessImpact, availabilityBusinessImpact)
			else:
				for asset in componentAssets:
					C = getCIAValueForAsset(asset,'confidentiality', rootAssets)
					I = getCIAValueForAsset(asset,'integrity', rootAssets)
					A = getCIAValueForAsset(asset,'availability', rootAssets)

					confidencialityBusinessImpact	 = businessImpactWeighting * (componentThreatProps['C'] * greatestWeaknessImpact) / 100 + assetValueWeighting * C
					integrityBusinessImpact 		 = businessImpactWeighting * (componentThreatProps['I'] * greatestWeaknessImpact) / 100 + assetValueWeighting * I
					availabilityBusinessImpact 		 = businessImpactWeighting * (componentThreatProps['A'] * greatestWeaknessImpact) / 100 + assetValueWeighting * A
					print(f'	Asset: {asset}: C={color(str(C),"green")} I={color(str(I),"yellow")} A={color(str(A),"blue")}')
					print(f'	C = {businessImpactWeighting} * ({color(str(componentThreatProps["C"]),"green")} * {color(str(greatestWeaknessImpact),"pink")}) / 100 + {assetValueWeighting} * {color(str(C),"green")} = {confidencialityBusinessImpact}')
					print(f'	I = {businessImpactWeighting} * ({color(str(componentThreatProps["I"]),"yellow")} * {color(str(greatestWeaknessImpact),"pink")}) / 100 + {assetValueWeighting} * {color(str(I),"yellow")} = {integrityBusinessImpact}')
					print(f'	A = {businessImpactWeighting} * ({color(str(componentThreatProps["A"]),"blue")} * {color(str(greatestWeaknessImpact),"pink")}) / 100 + {assetValueWeighting} * {color(str(A),"blue")} = {availabilityBusinessImpact}')
					# We get the maximum value from CIA impact values
					maxCIAValue = max(confidencialityBusinessImpact, integrityBusinessImpact, availabilityBusinessImpact)
					if maxCIAValue > greatestBusinessImpact:
						print(f'	New Maximum: {maxCIAValue}')
						greatestBusinessImpact = maxCIAValue
			print()

			# After getting the maximum value we have to normalize it to get final impact value
			greatestBusinessImpactAfterNorm = normalize(greatestBusinessImpact, businessImpactDenominator)
			print(f'	Greatest Business Impact Normalized: ||{greatestBusinessImpact}|| = {color(str(greatestBusinessImpactAfterNorm),"blue")}')
			greatestBusinessImpactFinal = businessImpactWeighting * (greatestBusinessImpactAfterNorm * greatestWeaknessImpact) / 100 + assetValueWeighting * maxAvgAssetValue
			print(f'	Greatest Business Impact Adjusted = {businessImpactWeighting} * ({color(str(greatestBusinessImpactAfterNorm),"blue")} * {color(str(greatestWeaknessImpact),"pink")}) / 100 + {assetValueWeighting} * {color(str(maxAvgAssetValue),"lred")} = {greatestBusinessImpactFinal}')
			impact = normalize(greatestBusinessImpactFinal, businessImpactDenominator)
			print(f'	Impact = ||{greatestBusinessImpactFinal}|| = {color(str(impact),"lgreen")}')
			print()
			# Calculate probability

			exposureRating = 100 - componentTz.get("rating")
			print(f'	Exposure rating: 100 - {componentTz.get("rating")} (TrustZone rating) = {exposureRating}')
			easeOfExploitation = componentThreatProps['EE']
			print(f'	Ease of exploitation: {color(str(easeOfExploitation),"lblue")}')
			probability = exposureWeighting * exposureRating + easeOfExploitationWeighting * easeOfExploitation
			probability = normalize(probability, probabilityDenominator)
			print(f'	Probability = ||{exposureWeighting} * {exposureRating} + {easeOfExploitationWeighting} * {color(str(easeOfExploitation),"lblue")}|| = {color(str(probability),"lgreen")}')
			print()
			# Calculate inherent risk
			IR = round(sqrt(impact * probability))
			print(f'		{color("Inherent Risk","blue")} = √({color(str(impact),"lgreen")} * {color(str(probability),"lgreen")}) = {color(str(IR),"blue")}')
			
			# ####### Current risk #######
			print(" + Calculating Current Risk...")
			# Controls
			componentControlsFromComponentRoot = list(component.find('controls').iter('control')) # Information
			# TODO: We assume there is no control without a weakness
			componentControlsFromComponentThreat = list(threat.find('weaknesses').iter('control')) # Mitigations

			RR = 0
			for control in componentControlsFromComponentThreat:
				mitigation = int(control.attrib['mitigation'])
				factor = getFactorCR(control, componentControlsFromComponentRoot)
				RR = RR+ ceil((mitigation * factor * IR) / 100)
				if factor != 0:
					print(f'	{control.attrib["ref"]} it {color("is","green")} applicable (Mitigation: {mitigation})')
					print(f'	RR = ceil(({mitigation} * {factor} * {color(str(IR),"blue")}) / 100) = {color(str(RR),"lred")}')
				else:
					print(f'	{control.attrib["ref"]} is {color("not","bgred")} applicable')
			print(f'	RR (risk reduction) = {color(str(RR),"lred")}')

			RI = ceil((vulnerabilityFoundFactor * IR * greatestFailedWeaknessImpact) / 100)
			print(f'	RI (risk increment) = ceil(({vulnerabilityFoundFactor} * {color(str(IR),"blue")} * {color(str(greatestWeaknessImpact),"pink")}) / 100) = {color(str(RI),"yellow")}')
			CR = IR - RR + RI
			if CR < 0:
				print("Current Risk is below zero. Adjusting...")
				CR = 0
			print(f'		{color("Current Risk","green")} = {color(str(IR),"blue")} - {color(str(RR),"lred")} + {color(str(RI),"yellow")} = {color(str(CR),"green")}')
			
			# ####### Projected risk #######
			
			print(" + Calculating Projected Risk...")
			RR = 0
			for control in componentControlsFromComponentThreat:
				mitigation = int(control.attrib['mitigation'])
				factor = getFactorPR(control, componentControlsFromComponentRoot)
				RR = RR + ceil((mitigation * factor * IR) / 100)
				if factor != 0:
					print(f'	{control.attrib["ref"]} it {color("is","green")} applicable (Mitigation: {mitigation})')
					print(f'	RR = ceil(({mitigation} * {factor} * {color(str(IR),"blue")}) / 100) = {color(str(RR),"lred")}')
				else:
					print(f"	{control.attrib['ref']} is {color('not','bgred')} applicable")
			print(f'	RR (risk reduction) = {color(str(RR),"lred")}')
			RI = ceil((vulnerabilityFoundFactor * IR * greatestFailedWeaknessImpact) / 100)
			print(f'	RI (risk increment) = ceil(({vulnerabilityFoundFactor} * {color(str(IR),"blue")} * {color(str(greatestWeaknessImpact),"pink")}) / 100) = {color(str(RI),"yellow")}')

			PR = IR - RR + RI
			if PR < 0:
				print("		Projected Risk is below zero. Adjusting...")
				PR = 0
			print(f'		{color("Projected Risk","lblue")} = {color(str(IR),"blue")} - {color(str(RR),"lred")} + {color(str(RI),"yellow")} = {color(str(PR),"lblue")}')

			# Adding the values to the totals
			inherentRiskList.append(IR)
			currentRiskList.append(CR)
			projectedRiskList.append(PR)
			
			print()

	print()
	print("###################################################")
	print(f'Total Threats: {threatCount}')
	print(f'Total {color("Inherent Risk","blue")}: sum({inherentRiskList})/{threatCount} = {color(str(round(sum(inherentRiskList) / threatCount)),"blue")}')
	print(f'Total {color("Current Risk","green")}: sum({currentRiskList})/{threatCount} = {color(str(round(sum(currentRiskList) / threatCount)),"green")}')
	print(f'Total {color("Projected Risk","lblue")}: sum({projectedRiskList})/{threatCount} = {color(str(round(sum(projectedRiskList) / threatCount)),"lblue")}')
	print("###################################################")
	print()


if __name__ == "__main__":
	if len(sys.argv) > 1 and sys.argv[1].endswith('.xml'):
		calculateRisk(sys.argv)
	else:
		print("This program calculates risk based on an architecture template. You have to provide some configuration values at the beginning of this file")
		print("Usage: python riskCalculator.py <product.xml>")
		print("<product.xml>: XML product file")
