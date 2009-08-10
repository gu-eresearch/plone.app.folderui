from Products.CMFCore.interfaces._content import IFolderish
from zope.interface import implements
from zope.component import adapts, queryUtility, IFactory
from interfaces import (IQueryResults, IComposedQuery, IFacetSettings,
    IQueryRunner, IFacetedListing,)
from query import ComposedQuery
from utils import dottedname


class FacetedListing(object):
    implements(IFacetedListing)
    adapts(IFolderish)
    
    def __init__(self, context, query=None):
        if not IFolderish.providedBy(context):
            raise ValueError('context does not appear to be a folder')
        self.context = context
        if query and not IComposedQuery.providedBy(query):
            raise ValueError('query does not provide IComposedQuery')
        elif query is None:
            query = ComposedQuery()
        self.query = query
    
    def _result(self):
        if not hasattr(self, '_result_map'):
            factory = queryUtility(IFactory, (dottedname(IQueryRunner)))
            runner = factory(self.context)
            self._result_map = runner(self.query)
        return self._result_map #IQueryResults == iterable mapping
    
    @property
    def result(self):
        return self._result().values() #LazyMap of brains
    
    @property
    def facets(self):
        if not hasattr(self, '_facets'):
            facets = queryUtility(IFacetSettings)
            if facets is None:
                return []
            self._facets = facets.values()
        return self._facets

