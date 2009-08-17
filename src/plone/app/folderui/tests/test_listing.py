import unittest

from zope.component import queryUtility, IFactory

from plone.app.folderui.interfaces import IFacetSpecification, IFacetSettings
from plone.app.folderui.listing import FacetedListing
from plone.app.folderui.querys import ComposedQuery

from base import BaseTestCases


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
    
    def _add_page_to_portal(self):
        self.add_content(id="test_in_root",
            portal_type='Document',
            target_folder=self.portal)
    
    def test_subfolders(self):
        self._add_page_to_portal()
        assert 'test_in_root' in self.portal.objectIds()
        assert self.portal['test_in_root'].portal_type == 'Document'
        listing_flat = FacetedListing(self.portal)
        listing_all  = FacetedListing(self.portal, include_subfolders=True)
        assert len(listing_all.result) > len(listing_flat.result)
        for brain in listing_flat.result:
            assert brain.getObject() in self.portal.objectValues()
            assert brain.getId in self.portal.objectIds()
            assert brain.getObject() in [b.getObject() for b in 
                listing_all.result]
        assert 'test_in_root' in [b.getId for b in 
                listing_all.result]
        assert 'test_in_root' in [b.getId for b in 
                listing_flat.result]
        o = self.target.objectValues()[0]
        assert o in [b.getObject() for b in 
                listing_all.result]
        assert o not in [b.getObject() for b in 
                listing_flat.result]
    
    def test_multiset_and_or(self):
        listing = FacetedListing(self.target)
        assert len(listing.result) == 6
        facets = queryUtility(IFacetSettings)
        categories = facets['categories']
        filters = categories(self.target)
        spec1 = [f for f in filters if f.name=='news item'][0]
        spec2 = [f for f in filters if f.name=='one'][0]
        qf1 = spec1(self.target) #query filter
        listing1 = FacetedListing(self.target, ComposedQuery(filters=[qf1]))
        assert len(listing1.result) == 2
        qf2 = spec2(self.target) #query filter
        listing2 = FacetedListing(self.target, ComposedQuery(filters=[qf2]))
        assert len(listing2.result) == 2
        qf1.conjunction = qf2.conjunction = 'OR'
        listing_or = FacetedListing(self.target,
            ComposedQuery(filters=[qf1, qf2]))
        asset len(listing_or.result) == 2
        qf1.conjunction = qf2.conjunction = 'AND'
        listing_and = FacetedListing(self.target,
            ComposedQuery(filters=[qf1, qf2]))
        assert len(listing_and) == 1


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestListing))
    return suite

