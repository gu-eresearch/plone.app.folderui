import unittest

#from zope.component import queryUtility, IFactory

from plone.app.folderui.interfaces import IFacetSpecification
from plone.app.folderui.listing import FacetedListing

from base import BaseTestCase


class TestListing(BaseTestCase):
    def afterSetUp(self):
        BaseTestCase.afterSetUp(self)
        self.add_samples()
    
    def test_facets(self):
        listing = FacetedListing(self.target)
        facets = listing.facets
        assert facets is not None
        assert len(facets) > 0
        for facet in facets:
            assert IFacetSpecification.providedBy(facet)
    
    def test_result(self):
        listing = FacetedListing(self.target)
        result = listing.result
        objects = [brain.getObject() for brain in result]
        for o in self.target.objectValues():
            assert o in objects
    
    def _compare_counts(self, original, another):
        assert len(another) == len(original)
        for key,count in another.items():
            assert key in original
            assert original[key] == count
    
    def test_counts(self):
        """test counts, intersections twice, expect identical results"""
        listing = FacetedListing(self.target)
        result = listing.result
        assert not hasattr(listing, '_counts') #under surface, no counts yet
        counts = listing.counts
        assert hasattr(listing, '_counts')
        assert counts #non-empty
        assert isinstance(counts, dict)
        original = dict(counts.items()) #make a copy
        ## get counts again, expect consistency!
        self._compare_counts(original, listing.counts)
        ## finally, for good measure remove underlying _counts and try again:
        delattr(listing, '_counts')
        self._compare_counts(original, listing.counts)


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestListing))
    return suite

