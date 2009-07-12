import urllib

from zope.component import queryUtility, IFactory, ComponentLookupError
from Products.Five import BrowserView
from Products.CMFPlone import Batch

from plone.app.folderui import defaults #triggers registration: TODO: move reg.
from plone.app.folderui.interfaces import IFacetSettings, IFilterSpecification
from plone.app.folderui.query import ComposedQuery
from plone.app.folderui.catalog import AdvancedQueryRunner
from plone.app.folderui.utils import dottedname


class FacetListing(BrowserView):
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.load_filter_state()
    
    @property
    def facets(self):
        facets = queryUtility(IFacetSettings)
        if facets is None:
            return []
        return facets.values()
    
    def listings(self):
        q = self.compose_from_query_state()
        runner = AdvancedQueryRunner(self.context)
        #runner = queryUtility(IQueryRunner) #TODO: decouple later
        result_map = runner(q)
        return result_map.values() #LazyMap of brains
    
    def batch(self, b_size=100):
        b_size = int(self.request.get('b_size',b_size))
        b_start = self.request.get('b_start', 0)
        batch = Batch(self.listings(), b_size, b_start, orphan=0)
        return batch
    
    def compose_from_query_state(self):
        """get composed query from current filter state"""
        q = ComposedQuery()
        for facet,filter_spec in self._state.values():
            query_filter = filter_spec() #make IQueryFilter object
            q += query_filter               #combine to composed query
        return q
    
    def _facet_query(self):
        req = self.request
        return dict(
            [(k.replace('facet.',''),v) for k,v in req.items() 
                if k.startswith('facet.')])
    
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
    
    def filter_link(self, facet, filter):
        """
        Make URL for the intersection of current facet state and a filter
        returning a complete filter link for facet+filter.
        """
        base = self.facet_state_querystring()
        k = urllib.quote('facet.%s' % facet.name)
        v = urllib.quote(filter.name)
        qs = '%s=%s' % (k,v)
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
        qs = qs.replace(rem, '')
        qs = qs.replace('?&','?')
        qs = qs.replace('&&', '&')
        if qs.endswith('&'):
            qs = qs[:-1]
        return qs

