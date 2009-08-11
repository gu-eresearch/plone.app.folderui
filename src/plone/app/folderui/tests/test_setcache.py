import unittest

from zope.event import notify
from zope.interface.verify import verifyObject
from zope.lifecycleevent import ObjectModifiedEvent

from zope.component import queryUtility, IFactory

import plone.app.folderui.vocab #trigger utility reg: TODO: to zcml
from plone.app.folderui.interfaces import ISetCacheTools, IQueryRunner
#from plone.app.folderui.defaults import * #FACETS
from plone.app.folderui.cache import PersistentRecordInvalidationSet
from plone.app.folderui.listing import FacetedListing
from plone.app.folderui.query import ComposedQuery
from plone.app.folderui.setuphandlers import bootstrap_cache_utilities
from plone.app.folderui.utils import dottedname, sitemanager_for
from base import BaseTestCase


class TestSetCacheTools(BaseTestCase):
    
    def afterSetUp(self):
        BaseTestCase.afterSetUp(self)
        self.add_samples()
        self.listing = FacetedListing(self.target, ComposedQuery())
    
    def _get_utility(self):
        sm = sitemanager_for(self.portal)
        u = queryUtility(ISetCacheTools, context=sm)
        assert u is not None
        verifyObject(ISetCacheTools, u)
        return u
    
    def test_utility_lookup(self):
        rval = self._get_utility()
    
    def _filters(self):
        result = []
        print len(FACETS)
        for facet in FACETS.values():
            for filter in facet(self.target):
                result.append((facet, filter))
            print 'facet %s has %s filters' % (facet.name, len(facet(self.target)))
        return result
    
    def test_expected_intersection_items(self):
        """
        for given sample set of , test result of intersection from cache
        matches actual items uncached.
        """
        self._clear_cache_completely() #just in case
        countmap_uncached = self.listing.counts    # 1: uncached, caches
        countmap_cached = self.listing.counts      # 2: from cache
        assert len(countmap_cached) == len(countmap_uncached)
        for key,count in countmap_cached.items():
            assert countmap_uncached[key] == count
    
    def _obj_rid(self, o):
        catalog = self.portal.portal_catalog
        brains = catalog(path='/'.join(o.getPhysicalPath()))
        if len(brains) > 0:
            return brains[0].getRID()
        return None
    
    def _clear_cache_completely(self):
        u = self._get_utility()
        for k in u.filter_setid_cache:
            del(u.filter_setid_cache[k])
        for k in u.set_cache:
            del(u.set_cache[k])
        u.invalidated_records = PersistentRecordInvalidationSet()
    
    def test_invalidation_on_modify(self):
        """
        Test that on edit of an item, that item record id is in the
        set cache tools record invalidation list, and also check that the
        search results change as expected.
        
        Note: modification plus event notification is required to invalidate.
        """
        self._clear_cache_completely() #just in case
        original_countmap = self.listing.counts
        #'categories' not in vocab:
        assert 'categories.changed' not in original_countmap 
        assert original_countmap['categories.one'] == 3
        tool = self._get_utility()
        o = self.target['document1']
        rid = self._obj_rid(o)
        assert o.Subject() == ('one','document')
        o.setSubject(('changed',))  # this is a new subject value not in vocab
        assert o.Subject() == ('changed',)
        notify(ObjectModifiedEvent(o)) #subscriber queues RID for invalidation
        o.reindexObject()
        assert rid is not None
        assert rid in tool.invalidated_records
        updated_countmap = self.listing.counts
        assert 'categories.changed' in updated_countmap
        assert updated_countmap['categories.changed'] == 1
        assert updated_countmap['categories.one'] == 2
        #now, make sure that RID was removed from invaldated records on 
        # update (after accessing self.listing.counts, which regenerated):
        assert rid not in tool.invalidated_records


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSetCacheTools))
    return suite

