import urllib

from zope.component import queryUtility
from Products.Five import BrowserView
from plone.app.folderui import defaults #triggers registration: TODO: move reg.
from plone.app.folderui.interfaces import IFacetSettings
from plone.app.folderui.query import ComposedQuery
from plone.app.folderui.catalog import AdvancedQueryRunner


class FacetViewInfo(object):
    """object containing render-ready facet info"""
    def __init__(self, name, spec, filters):
        self.name = name
        self.spec = spec
        self.filters = filters


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
        result = []
        for k,v in facets.items():
            filters = v(self.context) #call to get filter vocab
            result.append(FacetViewInfo(k,v,filters))
        return result
    
    def listings(self, **kwargs):
        #q = ComposedQuery()
        q = self.compose_from_query_state()
        runner = AdvancedQueryRunner(self.context)
        #runner = queryUtility(IQueryRunner) #TODO: decouple later
        result_map = runner(q)
        return result_map.values() #LazyMap of brains
    
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
    
    def load_filter_state(self):
        self._state = {}
        all_facets = queryUtility(IFacetSettings)
        facet_query = self._facet_query()
        for facet_name, filter_name in facet_query.items():
            if facet_name in all_facets:
                facet = all_facets[facet_name]
                vocabulary = facet(self.context)
                if filter_name in vocabulary:
                    filter_spec = vocabulary.getTerm(filter_name)
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
        k = 'facet.%s' % facet.name
        v = filter.name
        qs = '%s&%s=%s' % (base, k, v)
        return 'facet_listing?%s' % qs

