import sys
import ipo2_sup as mod


def export(outfilename):
    parser = None
    doc = mod.parsexml_('ipo.xml', parser)
    rootNode = doc.getroot()
    rootTag, rootClass = mod.get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'PurchaseOrderType'
    rootClass = mod.PurchaseOrderType
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    with open(outfilename, 'w') as outfile:
        outfile.write("<container>\n")
        rootObj.export(
            outfile, 1, name_=rootTag, namespaceprefix_='',
            namespacedef_='',
            pretty_print=True)
        outfile.write("    <!-- =============================== -->\n")
        rootObj.export(
            outfile, 1, name_=rootTag, namespaceprefix_='ABC:',
            namespacedef_='xmlns:ABC="http://www.example.com/IPO"',
            pretty_print=True)
        outfile.write("    <!-- =============================== -->\n")
        rootObj.export(
            outfile, 1, name_=rootTag, namespaceprefix_='ipo:',
            namespacedef_='xmlns:ipo="http://www.example.com/IPO"',
            pretty_print=True)
        outfile.write("</container>\n")


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        sys.exit('usage: ipo_test_namespace.py <out-file-name>')
    outfilename = args[0]
    export(outfilename)


if __name__ == "__main__":
    #import ipdb; ipdb.set_trace()
    main()
