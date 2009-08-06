import unittest

from zope.interface.verify import verifyObject
from zope.component import queryUtility

from plone.app.folderui.interfaces import ISetCacheTools
from plone.app.folderui.setuphandlers import bootstrap_cache_utilities
from plone.app.folderui.utils import sitemanager_for
from base import BaseTestCase


class TestSetCacheTools(BaseTestCase):
    
    def test_utility_lookup(self):
        sm = sitemanager_for(self.portal)
        u = queryUtility(ISetCacheTools, context=sm)
        assert u is not None
        verifyObject(ISetCacheTools, u)

        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSetCacheTools))
    return suite

