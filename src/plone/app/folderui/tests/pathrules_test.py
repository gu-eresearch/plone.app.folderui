"""
Tests for IterableCatalogResults proxy/adapter around fake catalog, results.
"""

import unittest
from plone.app.folderui.defaults import BasePathRules
from plone.app.folderui.interfaces import FACETS_ALL

class PathRulesTests(unittest.TestCase):

    def setUp(self):
        from plone.app.folderui.config import register_defaults
        register_defaults()

    def test_path_rules(self):
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
    
    def test_disable_facets_for_path(self):
        pathrules = BasePathRules()
        pathrules.include((),('owner','categories'))
        pathrules.include(('bakery',),('cupcakes','cookies'))
        pathrules.exclude(('bakery','cookies'), FACETS_ALL) #disable all
        assert set(pathrules(('bakery',))) == set(
            ('categories','owner','cupcakes','cookies'))
        assert set(pathrules(('bakery','cookies'))) == set() #should be empty
    
    def test_reset_for_path(self):
        pass

if __name__ == '__main__':
    unittest.main()

