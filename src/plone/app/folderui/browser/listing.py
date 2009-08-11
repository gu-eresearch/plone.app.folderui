import urllib

from zope.component import queryUtility, IFactory, ComponentLookupError
from Products.Five import BrowserView
from Products.CMFPlone.PloneBatch import Batch

from plone.app.folderui import defaults #triggers registration: TODO: move reg.
from plone.app.folderui.interfaces import (IFacetSettings,
    IFilterSpecification, ISetCacheTools)
from plone.app.folderui.query import ComposedQuery
from plone.app.folderui.catalog import AdvancedQueryRunner
from plone.app.folderui.utils import dottedname, sitemanager_for
from plone.app.folderui.listing import FacetedListing


class ListingView(BrowserView):
    
    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        self.load_filter_state()
        query = self.compose_from_query_state()
        self.provider = FacetedListing(self.context, query)
    
    @property
    def facets(self):
        if not hasattr(self, '_facets'):
            self._facets = self.provider.facets
        return self._facets
    
    @property
    def result(self):
        if not hasattr(self, '_result'):
            self._result = self.provider.result
        return self._result #LazyMap of brains
    
    @property
    def counts(self):
        if not hasattr(self, '_counts'):
            self._counts = self.provider.counts
        return self._counts
    
    def batch(self, b_size=100):
        b_size = int(self.request.get('b_size',b_size))
        b_start = self.request.get('b_start', 0)
        batch = Batch(self.result, b_size, b_start, orphan=0)
        return batch
    
    def compose_from_query_state(self):
        """get composed query from current filter state"""
        q = ComposedQuery()
        for facet,filter_spec in self._state.values():
            query_filter = filter_spec() #make IQueryFilter object
            q += query_filter               #combine to composed query
        return q
    
    def _facet_query(self):
        return dict([(k.replace('facet.',''),v) for k,v in
            self.request.items() if k.startswith('facet.')])
    
    def applied_filters(self):
        return self._state.values() #list of tuples of (facet, filter)
    
    def load_filter_state(self):
        self._state = {}
        all_facets = queryUtility(IFacetSettings)
        facet_query = self._facet_query()
        for facet_name, filter_name in facet_query.items():
            if facet_name in all_facets:
                facet = all_facets[facet_name]
                if not facet.use_vocabulary:
                    # no vocab, so create filter spec on fly instead of lookup
                    factory = queryUtility(IFactory,
                        dottedname(IFilterSpecification))
                    if factory is None:
                        raise ComponentLookupError('no filter factory')
                    filter_spec = factory(value=filter_name, index=facet.index)
                    self._state[facet_name] = (facet, filter_spec)
                    continue
                vocabulary = facet(self.context)
                if filter_name in vocabulary:
                    filter_spec = vocabulary.getTerm(filter_name)
                    self._state[facet_name] = (facet, filter_spec)
                elif str(filter_name) in vocabulary.by_token:
                    filter_spec = vocabulary.getTermByToken(str(filter_name))
                    self._state[facet_name] = (facet, filter_spec)
    
    def facet_state_querystring(self):
        """make base querystring from current facet state"""
        query = {}
        for facet,filter_spec in self._state.values():
            k = 'facet.%s' % facet.name
            query[k] = filter_spec.name or str(filter_spec.value)
        return urllib.urlencode(query)
    
    def _link_fragment(self, facet, filter):
        return urllib.urlencode({('facet.%s' % facet.name) : filter.name})
    
    def filter_link(self, facet, filter):
        """
        Make URL for the intersection of current facet state and a filter
        returning a complete filter link for facet+filter.
        """
        base = self.facet_state_querystring()
        if ('facet.%s' % facet.name) in base:
            previous_filter = self._state[facet.name][1]
            base = self.strike_filter(facet, previous_filter)
            ## TODO: assumes only one link per facet is possible
        qs = self._link_fragment(facet,filter)
        if base:
            qs = '%s&%s' % (base, qs)
        return 'facet_listing?%s' % qs
    
    def strike_filter(self, facet, filter):
        """
        Make a URL that includes all filter state in query string EXCEPT
        the facet/filter combination passed, with the effect returning a
        link that removes the filter.
        """
        qs = self.facet_state_querystring()
        rem = urllib.urlencode({('facet.%s' % facet.name) : filter.name})
        ## remove current filter and normalize remaining querystring:
        if rem not in qs:
            #filter.name did not work, try by value (e.g. text facet)
            rem = urllib.urlencode({('facet.%s' % facet.name) : filter.value})
        qs = qs.replace(rem, '')
        qs = qs.replace('?&','?')
        qs = qs.replace('&&', '&')
        if qs.endswith('&'):
            qs = qs[:-1]
        return qs
    
    def is_active_filter(self, facet, filter):
        fragment = self._link_fragment(facet, filter)
        return fragment in self.facet_state_querystring()
    
    def count(self, facet, filter):
        if not hasattr(self, '_counts'):
            counts = self.counts #load first time
        key = '%s.%s' % (facet.name, filter.name)
        if key in self._counts:
            return self._counts[key] #return preloaded length of intersection
        return 0

