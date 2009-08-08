import unittest

from zope.interface.verify import verifyObject
from zope.component import queryUtility, IFactory

from plone.app.folderui.interfaces import ISetCacheTools, IQueryRunner
from plone.app.folderui.setuphandlers import bootstrap_cache_utilities
from plone.app.folderui.utils import dottedname, sitemanager_for
#import plone.app.folderui.catalog # trigger registration: TODO, move to ZCML
from base import BaseTestCase


## mock: create three query filters
QUERY_FILTERS = {
}

class TestSetCacheTools(BaseTestCase):
    
    def afterSetUp(self):
        BaseTestCase.afterSetUp(self)
        self.add_samples()

    def _get_utility(self):
        sm = sitemanager_for(self.portal)
        u = queryUtility(ISetCacheTools, context=sm)
        assert u is not None
        verifyObject(ISetCacheTools, u)
        return u

    def test_utility_lookup(self):
        rval = self._get_utility()
     
    def _query_runner(self):
        factory = queryUtility(IFactory, dottedname(IQueryRunner))
        assert factory is not None
        runner = factory(self.portal)
        assert runner is not None
        return runner
    
    def test_expected_intersection_items(self):
        """for given sample set, test result of intersection"""
        setutil = self._get_utility()
        runner = self._query_runner()
        # test that the queries run without caching 
        for query in QUERY_FILTERS.keys():
            result = runner(query)
            assert len(result) == QUERY_FILTERS[query]
         

        
def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSetCacheTools))
    return suite

