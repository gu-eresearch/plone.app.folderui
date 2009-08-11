from Products.CMFCore.interfaces._content import IFolderish
from zope.interface import implements
from zope.component import adapts, queryUtility, IFactory, ComponentLookupError

from interfaces import (IQueryResults, IComposedQuery, IFacetSettings,
    IQueryRunner, IFacetedListing, ISetCacheTools,)
from query import ComposedQuery
from utils import dottedname, sitemanager_for


class FacetedListing(object):
    """listing provider / (multi-)adapter for folder, query"""
    
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
        sm = sitemanager_for(self.context)
        self.cachetools = sm.queryUtility(ISetCacheTools)
        if self.cachetools is None:
            raise ComponentLookupError('cannot find local set cache utility')
    
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
    
    def _clear_invalidation(self, intersect):
        invalidated = self.cachetools.invalidated_records
        clear = set(invalidated) & set(intersect)
        if clear:
            s = set(self.cachetools.invalidated_records)
            for k in clear:
                s.remove(k)
            self.cachetools.invalidated_records = frozenset(s)
    
    @property
    def counts(self):
        if not hasattr(self, '_counts'):
            intersect = self._result()
            self._counts = {}
            for facet in self.facets:
                for filter in facet(self.context):
                    key = '%s.%s' % (facet.name, filter.name)
                    self._counts[key] = filter.count(self.context, facet, intersect)
            self._clear_invalidation(intersect)
        return self._counts

