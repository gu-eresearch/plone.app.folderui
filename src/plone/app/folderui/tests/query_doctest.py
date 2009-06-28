import unittest
from doctest import DocTestSuite

def docsuite():
    return unittest.TestSuite((DocTestSuite('plone.app.folderui.query'),))

if __name__ == '__main__':
    unittest.main(defaultTest='docsuite')

