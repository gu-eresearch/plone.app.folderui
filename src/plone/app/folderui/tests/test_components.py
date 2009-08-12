import unittest
from zope.app.container.interfaces import IObjectModifiedEvent
from zope.schema.interfaces import IVocabularyFactory
from zope.component import queryUtility, IFactory


from plone.app.folderui.interfaces import (IQueryRunner, IFilterSpecification,
    IQueryFilter, IComposedQuery, IFacetSettings,)
from plone.app.folderui.utils import sitemanager_for, dottedname

import base


class TestRegistrations(base.BaseTestCase):
    """
    Integration test for factories and utilities registered in ZCML;
    ensure expected behavior for lookups of global components.
    
    Note: vocabulary factory registrations are tested in test_vocab.py
    """
    
    def test_factory_registrations(self):
        f_runner = queryUtility(IFactory, dottedname(IQueryRunner))
        assert f_runner is not None
        assert IQueryRunner.implementedBy(f_runner)
        assert IQueryRunner.providedBy(f_runner(self.target))
        f_spec = queryUtility(IFactory, dottedname(IFilterSpecification))
        assert f_spec is not None
        assert IFilterSpecification.implementedBy(f_spec)
        assert IFilterSpecification.providedBy(f_spec())
        f_composed = queryUtility(IFactory, dottedname(IComposedQuery))
        assert f_composed is not None
        assert IComposedQuery.implementedBy(f_composed)
        assert IComposedQuery.providedBy(f_composed())
        f_query = queryUtility(IFactory, dottedname(IQueryFilter))
        assert f_query is not None
        assert IQueryFilter.implementedBy(f_query)
        assert IQueryFilter.providedBy(f_query())
    
    def test_utility_registrations(self):
        facet_settings = queryUtility(IFacetSettings)
        assert facet_settings is not None
        assert IFacetSettings.providedBy(facet_settings)


def test_suite():
    return unittest.makeSuite(TestRegistrations)


