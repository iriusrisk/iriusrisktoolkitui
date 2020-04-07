from lxml import etree, objectify
import os
import sys
home=os.getcwd()
from src.common import printWithColor

# In this method, we compare the xml input with the input xsd validator to validate the input xml.
def xmlValidator(xml_path, xsd_path):
    xml_path=str(xml_path)
    xsd_path=str(xsd_path)
    try:
        #Check if the path exists
        if(os.path.exists(xml_path)):
            # parse the XSD Schema input file
            xmlschema_parse = etree.parse(xsd_path)
            xmlschema = etree.XMLSchema(xmlschema_parse)
            # parse the xml input file
            xml_doc = etree.parse(xml_path)
            # validate the xml with the XSD schema
            result = xmlschema.validate(xml_doc)
            
            if result == False:
                os.system("xmllint --schema "+xsd_path+" "+xml_path+" --noout")
        else:
            result = False
            print("The following path was not found: "+str(xml_path))
        
    except etree.XMLSyntaxError:
        #handle exception here
        result = False
        os.system("xmllint --schema "+xsd_path+" "+xml_path+" --noout")

    return result

def xmlValidationCheck(filename_xml, filename_xsd):

    print('Validating XML File: ', filename_xml, ' against XSD schema: ', filename_xsd)    

    xmlschema_doc = etree.parse(filename_xsd)
    xmlschema = etree.XMLSchema(xmlschema_doc)

    # parse xml
    try:
        doc = etree.parse(filename_xml)
        print('XML well formed, syntax test: PASSED.')

    # check for file IO error
    except IOError:
        print('Invalid File')

    # check for XML syntax errors
    except etree.XMLSyntaxError as err:
        print('XML Syntax Error, syntax test: FAILED')
        print(err.error_log)
        quit()

    except:
        print('Unknown error, exiting.')
        quit()

    # validate against schema
    try:
        xmlschema.assertValid(doc)
        print('XML valid, schema validation test: PASSED.')

    except etree.DocumentInvalid as err:
        print('Schema validation test: FAILED')
        print(err.error_log)
        #quit()

    except:
        print('Unknown error, exiting.')
        quit()

USAGE_TEXT = """
You should pass two args.
Please give the arguments in the following order:
1 - The file name of the XML file with the extension (.xml).
2 - The file name of the Schema file with the extension (.xsd).
Usage: python sample_app1.py test.xlsx SheetName
"""

def usage():
    print(USAGE_TEXT)
    sys.exit(1)

def main():
    if len(sys.argv) != 3:
        usage()
    else:
        filename_xml = sys.argv[1]
        filename_xsd = sys.argv[2]
        xmlValidationCheck(filename_xml, filename_xsd)

if __name__ == '__main__':
    main()