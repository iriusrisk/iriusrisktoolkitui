#!/usr/bin/python
import sys
import xml.etree.ElementTree as ET
import io
from math import sqrt, ceil, floor
from pathlib import Path

############### Script configuration ###############

businessImpactWeighting=8
assetValueWeighting=1
exposureWeighting=1
easeOfExploitationWeighting=1
mitigationFactorIfControlTestPassed=1
mitigationFactorIfControlTestNotPassed=1
mitigationFactorIfControlImplemented=1
vulnerabilityFoundFactor=0
trustZones = {
	"58467363-ca32-4333-87ce-0c96c403d93c":{"name":"Internet","rating":1},
	"5490e4fe-0eec-431e-9d8d-b23a3ea6aa3a":{"name":"Public","rating":1},
	"8cacc40f-83c6-4d7a-993f-7e87ead7729a":{"name":"Public Cloud","rating":60},
	"55ed3fa2-f982-4405-8f06-d3325577b7a0":{"name":"Trusted Partner","rating":80},
	"30ae42cf-2f6f-49eb-8340-92a22c0f66d6":{"name":"Private Secured","rating":100}
}


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
def getFactorCRHTML(control, rootControl,f):
	ref = control.attrib['ref']
	for c in rootControl:
		if c.attrib['ref'] == ref:
			state = c.attrib['state']
			testResult = list(c.iter('source'))[0].attrib['result'] 
			f.write(tagOnlyBr(f'Control {ref} has state {state} and test {testResult}'))

			if testResult == 'Passed':
				return mitigationFactorIfControlTestPassed
			elif testResult != 'Failed' and state == 'Implemented':
				return mitigationFactorIfControlImplemented
			else:
				return 0
			
	return 0

# Return mitigation factor (1) if control is Required or Implemented
def getFactorPRHTML(control, rootControl,f):
	ref = control.attrib['ref']
	for c in rootControl:
		if c.attrib['ref'] == ref:
			state = c.attrib['state']
			f.write(tagOnlyBr(f'Control {ref} has state {state}'))
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
	componentTrustZone = component.find('trustZones').find('trustZone').attrib['ref']

	componentTz = {}
	if componentTrustZone in trustZones.keys():
		trustZoneDicc = trustZones[componentTrustZone]
		componentTz['trustzone']=trustZoneDicc['name']
		componentTz['rating']=trustZoneDicc['rating']
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

def tag(word, html):
	return f"<{html}>{word}</{html}>"

def tagBr(word, html):
	return f"<{html}>{word}</{html}><br>"

def tagOnlyBr(word):
	return f"{word}<br>"



def fontColor(word, color):
	return f'<b><font color="{color}">{word}</font></b>'

def bgColor(word, color):
	return f'<span style="background-color: {color}">{word}</span>'

def calculateRiskToHTML(xmlPath, htmlPath):
	tree = ET.parse(xmlPath)
	root = tree.getroot()
	f = io.open(htmlPath, "w", encoding="utf-8")

	code = "<!DOCTYPE html><html><head><title>Risk calculation for " + Path(xmlPath).name + "</title><link rel=\"stylesheet\" href=\"https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css\" integrity=\"sha384-Gn5384xqQ1aoWXA+058RXPxPg6fy4IWvTNh0E263XmFcJlSAwiGgFAW/dAiS6JXm\" crossorigin=\"anonymous\">"

	code = code + "<script src=\"https://code.jquery.com/jquery-3.3.1.slim.min.js\" integrity=\"sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo\" crossorigin=\"anonymous\"></script>"
	code = code + "<script src=\"https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js\" integrity=\"sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49\" crossorigin=\"anonymous\"></script>"
	code = code + "<script src=\"https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js\" integrity=\"sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy\" crossorigin=\"anonymous\"></script></head><body>"
	f.write(code)

	f.write(tag(f'Risk calculation for {Path(xmlPath).name}',"h1"))
	f.write(tag(f'Configuration', "h2"))
	f.write(tagOnlyBr(f'Business Impact Weighting: {businessImpactWeighting}'))
	f.write(tagOnlyBr(f'Asset Value Weighting: {assetValueWeighting}'))
	f.write(tagOnlyBr(f'Exposure Weighting: {exposureWeighting}'))
	f.write(tagOnlyBr(f'Ease of Exploitation Weighting: {easeOfExploitationWeighting}'))
	f.write(tagOnlyBr(f'Test Passed Factor: {mitigationFactorIfControlTestPassed}'))
	f.write(tagOnlyBr(f'Test Not Passed Factor: {mitigationFactorIfControlTestNotPassed}'))
	f.write(tagOnlyBr(f'Implemented Factor: {mitigationFactorIfControlImplemented}'))
	f.write(tagOnlyBr(f'Vulnerability Found Factor: {vulnerabilityFoundFactor}'))
	f.write("<br>")
	# First step: extract data for later use
	inherentRiskList = []
	currentRiskList = []
	projectedRiskList = []
	threatCount = 0
	businessImpactDenominator = businessImpactWeighting + assetValueWeighting
	probabilityDenominator = exposureWeighting + easeOfExploitationWeighting
	rootAssets = list(root.find('assets').iter('asset'))

	# For every component we need to calculate the risks for every threat in it
	# We prepare the assets and trustzone for the component
	for component in root.iter('component'):
		f.write(tag("### Component " + bgColor(component.attrib['name'],"green"),"h2"))
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
			f.write(tag(f'Threat: {bgColor(threat.attrib["ref"],"red")} - {threat.attrib["name"]}',"h3"))

			# Calculate the maximum weakness impact for this threat
			componentWeaknessFromComponentThreat = list(threat.find('weaknesses').iter('weakness')) # References
			greatestWeaknessImpact = getMaxWeaknessImpact(componentWeaknessFromComponentRoot, componentWeaknessFromComponentThreat)
			greatestFailedWeaknessImpact = getMaxFailedWeaknessImpact(componentWeaknessFromComponentRoot, componentWeaknessFromComponentThreat)

			# ####### Inherent Risk #######
			f.write(tag(" + Calculating One-time calculation data...","h4"))
			f.write(tagOnlyBr(f'MaxWeaknessImpact: {fontColor(str(greatestWeaknessImpact),"purple")}'))
			f.write(tagOnlyBr(f'MaxFailedWeaknessImpact: {str(greatestFailedWeaknessImpact)}'))
			f.write(tagOnlyBr(f'MaxAverageAssetValue: {str(maxAvgAssetValue)}'))
			f.write(tagOnlyBr(f'businessImpactDenominator: {businessImpactDenominator}'))
			f.write(tagOnlyBr(f'probabilityDenominator: {probabilityDenominator}'))
			f.write(tagOnlyBr(f'TrustZone: {componentTz["trustzone"]} -> Rating: {componentTz["rating"]}'))
			# Extract threat risk rating
			componentThreatProps = getThreatRiskRating(threat)
			f.write(f'Threat CIA & EE: C={fontColor(str(componentThreatProps["C"]),"limegreen")} I={fontColor(str(componentThreatProps["I"]),"orange")} A={fontColor(str(componentThreatProps["A"]),"darkturquoise")} EE={str(componentThreatProps["EE"])}')
			f.write("<br><br>")

			f.write(tag(" + Calculating Inherent Risk...","h4"))
			# Calculate impact: first we neet to calculate which asset has the greatest business impact
			greatestBusinessImpact=0
			f.write('	Calculating Greatest Business Impact...')
			if len(componentAssets)==0:
				C = 50
				I = 50
				A = 50

				confidencialityBusinessImpact	 = businessImpactWeighting * (componentThreatProps['C'] * greatestWeaknessImpact) / 100 + assetValueWeighting * C
				integrityBusinessImpact 		 = businessImpactWeighting * (componentThreatProps['I'] * greatestWeaknessImpact) / 100 + assetValueWeighting * I
				availabilityBusinessImpact 		 = businessImpactWeighting * (componentThreatProps['A'] * greatestWeaknessImpact) / 100 + assetValueWeighting * A
				f.write(tag(f'Asset: Default: C={str(C)} I={str(I)} A={str(A)}',"p"))
				f.write(tagOnlyBr(f'C = {businessImpactWeighting} * ({fontColor(str(componentThreatProps["C"]),"limegreen")} * {fontColor(str(greatestWeaknessImpact),"purple")}) / 100 + {assetValueWeighting} * {bgColor(str(C),"limegreen")} = {confidencialityBusinessImpact}'))
				f.write(tagOnlyBr(f'I = {businessImpactWeighting} * ({fontColor(str(componentThreatProps["I"]),"orange")} * {fontColor(str(greatestWeaknessImpact),"purple")}) / 100 + {assetValueWeighting} * {bgColor(str(I),"orange")} = {integrityBusinessImpact}'))
				f.write(tagOnlyBr(f'A = {businessImpactWeighting} * ({fontColor(str(componentThreatProps["A"]),"darkturquoise")} * {fontColor(str(greatestWeaknessImpact),"purple")}) / 100 + {assetValueWeighting} * {bgColor(str(A),"darkturquoise")} = {availabilityBusinessImpact}'))
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
					f.write(tag(f'Asset: {asset}: C={bgColor(str(C),"limegreen")} I={bgColor(str(I),"orange")} A={bgColor(str(A),"darkturquoise")}',"p"))
					f.write(tagOnlyBr(f'C = {businessImpactWeighting} * ({fontColor(str(componentThreatProps["C"]), "limegreen")} * {fontColor(str(greatestWeaknessImpact), "purple")}) / 100 + {assetValueWeighting} * {bgColor(str(C), "limegreen")} = {confidencialityBusinessImpact}'))
					f.write(tagOnlyBr(f'I = {businessImpactWeighting} * ({fontColor(str(componentThreatProps["I"]), "orange")} * {fontColor(str(greatestWeaknessImpact), "purple")}) / 100 + {assetValueWeighting} * {bgColor(str(I), "orange")} = {integrityBusinessImpact}'))
					f.write(tagOnlyBr(f'A = {businessImpactWeighting} * ({fontColor(str(componentThreatProps["A"]), "darkturquoise")} * {fontColor(str(greatestWeaknessImpact), "purple")}) / 100 + {assetValueWeighting} * {bgColor(str(A), "darkturquoise")} = {availabilityBusinessImpact}'))
					# We get the maximum value from CIA impact values
					maxCIAValue = max(confidencialityBusinessImpact, integrityBusinessImpact, availabilityBusinessImpact)
					if maxCIAValue > greatestBusinessImpact:
						f.write(tag(f'New Maximum: {maxCIAValue}',"p"))
						greatestBusinessImpact = maxCIAValue
			

			# After getting the maximum value we have to normalize it to get final impact value
			greatestBusinessImpactAfterNorm = normalize(greatestBusinessImpact, businessImpactDenominator)
			f.write(tagOnlyBr(f'Greatest Business Impact Normalized: {greatestBusinessImpact}/{businessImpactDenominator} = {str(greatestBusinessImpactAfterNorm)}'))
			greatestBusinessImpactFinal = businessImpactWeighting * (greatestBusinessImpactAfterNorm * greatestWeaknessImpact) / 100 + assetValueWeighting * maxAvgAssetValue
			f.write(tagOnlyBr(f'Greatest Business Impact Adjusted = {businessImpactWeighting} * ({str(greatestBusinessImpactAfterNorm)} * {str(greatestWeaknessImpact)}) / 100 + {assetValueWeighting} * {str(maxAvgAssetValue)} = {greatestBusinessImpactFinal}'))
			impact = normalize(greatestBusinessImpactFinal, businessImpactDenominator)
			f.write(tag(f'Impact = {greatestBusinessImpactFinal}/{businessImpactDenominator} = {str(impact)}',"p"))
			
			# Calculate probability

			exposureRating = 100 - componentTz.get("rating")
			f.write(tagOnlyBr(f'Exposure rating: 100 - {componentTz.get("rating")} (TrustZone rating) = {exposureRating}'))
			easeOfExploitation = componentThreatProps['EE']
			f.write(tagOnlyBr(f'Ease of exploitation: {str(easeOfExploitation)}'))
			probability = exposureWeighting * exposureRating + easeOfExploitationWeighting * easeOfExploitation
			probability = normalize(probability, probabilityDenominator)
			f.write(tag(f'Probability = ({exposureWeighting} * {exposureRating} + {easeOfExploitationWeighting} * {str(easeOfExploitation)})/{probabilityDenominator} = {str(probability)}',"p"))
			
			# Calculate inherent risk
			IR = round(sqrt(impact * probability))
			f.write(tag(f'{fontColor("Inherent Risk","red")} = √({str(impact)} * {str(probability)}) = {fontColor(str(IR),"red")}',"p"))
			
			# ####### Current risk #######
			f.write(tag(" + Calculating Current Risk...","h4"))
			# Controls
			componentControlsFromComponentRoot = list(component.find('controls').iter('control')) # Information
			# TODO: We assume there is no control without a weakness
			componentControlsFromComponentThreat = list(threat.find('weaknesses').iter('control')) # Mitigations

			RR = 0
			for control in componentControlsFromComponentThreat:
				mitigation = int(control.attrib['mitigation'])
				factor = getFactorCRHTML(control, componentControlsFromComponentRoot,f)
				RR = RR+ ceil((mitigation * factor * IR) / 100)
				if factor != 0:
					f.write(tagOnlyBr(f'{control.attrib["ref"]} it is applicable (Mitigation: {mitigation})'))
					f.write(tagOnlyBr(f'Adding ceil(({mitigation} * {factor} * {fontColor(str(IR),"red")}) / 100) = {ceil((mitigation * factor * IR) / 100)} to RR'))
				else:
					f.write(tagOnlyBr(f'{control.attrib["ref"]} is not applicable'))
				f.write("<br>")
			f.write(tag(f'RR (risk reduction) = {fontColor(str(RR),"blue")}',"p"))

			RI = ceil((vulnerabilityFoundFactor * IR * greatestFailedWeaknessImpact) / 100)
			f.write(tag(f'RI (risk increment) = ceil(({vulnerabilityFoundFactor} * {fontColor(str(IR),"red")} * {str(greatestWeaknessImpact)}) / 100) = {fontColor(str(RI),"green")}',"p"))
			CR = IR - RR + RI
			if CR < 0:
				f.write(tag("Current Risk is below zero. Adjusting...","p"))
				CR = 0
			f.write(tag(f'{fontColor("Current Risk","gold")} = {fontColor(str(IR),"red")} - {fontColor(str(RR),"blue")} + {fontColor(str(RI),"green")} = {fontColor(str(CR),"gold")}',"p"))
			
			# ####### Projected risk #######
			
			f.write(tag(" + Calculating Projected Risk...","h4"))
			RR = 0
			for control in componentControlsFromComponentThreat:
				mitigation = int(control.attrib['mitigation'])
				factor = getFactorPRHTML(control, componentControlsFromComponentRoot,f)
				RR = RR + ceil((mitigation * factor * IR) / 100)
				if factor != 0:
					f.write(tagOnlyBr(f'{control.attrib["ref"]} it is applicable (Mitigation: {mitigation})'))
					f.write(tagOnlyBr(f'Adding ceil(({mitigation} * {factor} * {fontColor(str(IR),"red")}) / 100) = {ceil((mitigation * factor * IR) / 100)} to RR'))
				else:
					f.write(tagOnlyBr(f'{control.attrib["ref"]} is not applicable'))
				f.write("<br>")
			f.write(tag(f'RR (risk reduction) = {fontColor(str(RR),"blue")}',"p"))

			RI = ceil((vulnerabilityFoundFactor * IR * greatestFailedWeaknessImpact) / 100)
			f.write(tag(f'RI (risk increment) = ceil(({vulnerabilityFoundFactor} * {fontColor(str(IR),"red")} * {str(greatestWeaknessImpact)}) / 100) = {fontColor(str(RI),"green")}',"p"))

			PR = IR - RR + RI
			if PR < 0:
				f.write(tag("Projected Risk is below zero. Adjusting...","p"))
				PR = 0
			f.write(tag(f'{fontColor("Projected Risk","orange")} = {fontColor(str(IR),"red")} - {fontColor(str(RR),"blue")} + {fontColor(str(RI),"green")} = {fontColor(str(PR),"orange")}',"p"))

			# Adding the values to the totals
			inherentRiskList.append(IR)
			currentRiskList.append(CR)
			projectedRiskList.append(PR)

	f.write("<br><br>")
	f.write(tag("Final results:","h1"))
	f.write(tag(f'Total Threats: {threatCount}',"h2"))
	if threatCount > 0:
		f.write(tag(f'Total {fontColor("Inherent Risk","red")}: sum({inherentRiskList})/{threatCount} = {str(round(sum(inherentRiskList) / threatCount))}',"h3"))
		f.write(tag(f'Total {fontColor("Current Risk","gold")}: sum({currentRiskList})/{threatCount} = {str(round(sum(currentRiskList) / threatCount))}',"h3"))
		f.write(tag(f'Total {fontColor("Projected Risk","orange")}: sum({projectedRiskList})/{threatCount} = {str(round(sum(projectedRiskList) / threatCount))}',"h3"))
	else:
		f.write(tag('There are no threats in this product', "h2"))

	f.write("</body>")

	f.close()

	return htmlPath

def main():
	xmlPath=sys.argv[1]
	htmlPath=sys.argv[2]
	calculateRiskToHTML(xmlPath,htmlPath);

if __name__ == '__main__':
  main()

			

