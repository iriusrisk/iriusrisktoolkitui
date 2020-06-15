import unittest
from src.tests.cases.integrity_tests import *
from src.xmlValidator import *
import os

class TestAllLibraries(unittest.TestCase):

  def setUp(self):
    self.path = Path.cwd() / "libraries"
    self.weaknesses, self.weaknessColumns = getWeaknessesFromAllLibraries(self.path)
    self.controls, self.controlColumns = getControlsFromAllLibraries(self.path)
    self.standards = getStandardsFromCountermeasures(self.path)

  def test_copyright(self):
    errors=checkCopyrightInAllLibrarires(self.path)
    self.assertEqual(errors, "", errors)

  def test_xsd_schema(self):
    errors=""
    filename_xsd=Path.cwd() / "inputFiles" / "XSD_Schema" / "library.xsd"
    for lib in os.listdir(str(self.path)):
      if lib.endswith(".xml"):
        if not xmlValidator(str(self.path / lib), str(filename_xsd)):
          errors+="XSD Schema validation fails in the library: %s.\n"%lib.replace(".xml", "")
    self.assertEqual(errors, "", errors)

  # We check if the original library pass the XSD Schema verification
  def test_duplicated_weakness_different_data(self):
    errors = extractResultsFromDataFrame(self.weaknesses, 'Weakness', self.weaknessColumns)
    self.assertEqual(errors, "", errors)

  def test_duplicated_countermeasures_different_data(self):
    errors = extractResultsFromDataFrame(self.controls, 'Countermeasure', self.controlColumns)
    self.assertEqual(errors, "", errors)

  def test_duplicated_countermeasures_different_standards(self):
    errors = extractCountermeasuresWithDifferentStandards(self.controls)
    self.assertEqual(errors, "", errors)

  def test_check_ascii_of_controls_descriptions(self):
    errors=checkAsciiOfControlsOrWeaknesses(self.controls, 'Description', [])
    self.assertEqual(errors, "", errors)

  def test_check_ascii_of_controls_test_steps(self):
    errors=checkAsciiOfControlsOrWeaknesses(self.controls, 'Test Steps', [])
    self.assertEqual(errors, "", errors)

  def test_check_ascii_of_weaknesses_descriptions(self):
    errors=checkAsciiOfControlsOrWeaknesses(self.weaknesses, 'Description', [])
    self.assertEqual(errors, "", errors)

  def test_check_ascii_of_weaknesses_test_steps(self):
    errors=checkAsciiOfControlsOrWeaknesses(self.weaknesses, 'Test Steps', [])
    self.assertEqual(errors, "", errors)
  
  def test_check_empty_weaknesses(self):
    exceptions = ['CWE-7-KINGDOMS']
    errors = checkEmptyWeaknesses(self.path, exceptions)
    self.assertEqual(errors, "", errors)

  def test_check_orphaned_controls(self):
    errors = checkOrphanedControls(self.path)
    self.assertEqual(errors, "", errors)

  def test_check_CRLF(self):
    errors = checkCRLF(self.path)
    self.assertEqual(errors, "", errors)

  def test_check_duplicated_standards_in_control(self):
    errors = checkDuplicatedStandardsInControl(self.path)
    self.assertEqual(errors, "", errors)

  def test_check_whitespaces_in_reference_URLs(self):
    errors = checkWhitespacesInReferenceUrls(self.path)
    self.assertEqual(errors, "", errors)

  def test_check_inconsistent_control_names(self):
    errors = checkInconsistentControlNames(self.path)
    self.assertEqual(errors, "", errors)

  def test_aa_duplicated_risk_pattern_refs(self):
    errors = checkDuplicatedRiskPatternRefs(self.path)
    self.assertEqual(errors, "", errors)

  """
  # Test disabled because we don't need it now
  def test_check_inconsistent_threat_and_weakness_names(self):
    errors = checkInconsistentThreatAndWeaknessNames(self.path)
    self.assertEqual(errors, "", errors)
  """


if __name__ == "__main__":
  unittest.main()
