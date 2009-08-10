import unittest

#from zope.component import queryUtility, IFactory

from plone.app.folderui.interfaces import IFacetSpecification
from plone.app.folderui.listing import FacetedListing

from base import BaseTestCase


class TestListing(BaseTestCase):
    
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


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestListing))
    return suite

