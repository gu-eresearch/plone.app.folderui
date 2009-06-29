"""
Tests for IterableCatalogResults proxy/adapter around fake catalog, results.
"""

import unittest
from plone.app.folderui.defaults import BasePathRules


class TestIterableCatalogResults(unittest.TestCase):
    
    def testPathRules(self):
        pathrules = BasePathRules()
        
        # rules for site root
        assert pathrules.whitelist == {}
        assert pathrules.blacklist == {}
        pathrules.include((),('owner','categories'))
        assert 'owner' in pathrules.whitelist[()]
        assert 'categories' in pathrules.whitelist[()]
        
        # path relative to site root: /bakery
        pathrules.include(('bakery',),('cupcakes','cookies'))
        assert 'cupcakes' not in pathrules.whitelist[()]
        assert 'cupcakes' in pathrules.whitelist[('bakery',)]
        pathrules.exclude(('bakery',), ('owner',))
        assert 'owner' in pathrules.blacklist[('bakery',)]
        assert set(pathrules(('bakery',))) == set(
            ('categories','cupcakes','cookies'))
        
        # path relative to site root: /bakery/cookies
        pathrules.exclude(('bakery','cookies'), ('cupcakes',))
        pathrules.include(('bakery','cookies'), ('nuts',))
        assert set(pathrules(('bakery','cookies'))) == set(
            ('categories','cookies','nuts'))


if __name__ == '__main__':
    unittest.main()

