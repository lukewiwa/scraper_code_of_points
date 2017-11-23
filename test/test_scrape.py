import pytest
import os
from scrape import Code
import lxml.etree as ET

class Code_test(Code):
    def __init__(self, xml):
        self.tree = None
        self.root = ET.fromstring(xml)


def test_element_path_false():
    xml = '<Total><test><b>A</b></test></Total>'
    code = Code_test(xml)
    assert code.getGH(code.root) is None

def test_element_path_true():
    xml = '<Total><test><b>H</b></test></Total>'
    code = Code_test(xml)
    assert code.getGH(code.root) == "H"
