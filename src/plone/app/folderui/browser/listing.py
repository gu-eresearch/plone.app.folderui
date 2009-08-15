import urllib

from zope.component import queryUtility, IFactory, ComponentLookupError
from zope.interface import implements
from zope.schema.fieldproperty import FieldProperty
from Products.Five import BrowserView
from Products.CMFPlone.PloneBatch import Batch

from plone.app.folderui.interfaces import IFacetSettings, IFilterSpecification
from plone.app.folderui.query import ComposedQuery
from plone.app.folderui.utils import dottedname
from plone.app.folderui.listing import FacetedListing


from interfaces import IFacetState


class FacetState(object):
    """given query state for a single given facet"""
    implements(IFacetState)
    
    conjunction = FieldProperty(IFacetState['conjunction'])
    
    @property
    def name(self):
        if not self.facet and not self.facet.name:
            return None
        return self.facet.name
    
    def __init__(self, facet, filters=()):
        self.conjunction = 'OR' #default
        self.facet = facet
        self.filters = tuple(filters)


def count_sort_cmp(a,b):
    if a>b: return 0


class ListingView(BrowserView):
    
    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        self._request_fixups()
        self.load_filter_state()
        query = self.compose_from_query_state()
        self.include_subfolders = 'include_subfolders' in request
        self.provider = FacetedListing(self.context,
            query,
            self.include_subfolders)
        self._sorted_filters = {}
    
    def _request_fixups(self):
        if 'facet.text' in self.request.form:
            v = self.request.form.get('facet.text', None)
            if not v:
                del(self.request.form['facet.text'])
    
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
    
    def filters_for(self, facet, cmpfn=None):
        """sorted filters for facet"""
        if (facet.name, cmpfn) not in self._sorted_filters:
            if cmpfn is None:
                #default, sort filter links by most hits
                cmpfn = lambda a,b: cmp(self.count(facet, b), self.count(facet, a))
            self._sorted_filters[(facet.name,cmpfn)] = sorted(
                facet(self.context), cmpfn)
        return self._sorted_filters[(facet.name, cmpfn)]
    
    def narrow_filters(self, facet):
        """filters that can actively narrow the current result (count>0)"""
        return [f for f in self.filters_for(facet) if self.count(facet,f)>0]
    
    def expand_filters(self, facet):
        """filters that can modify or expand a result, not narrow (count==0)"""
        return [f for f in self.filters_for(facet) if self.count(facet,f)==0]
    
    def compose_from_query_state(self):
        """get composed query from current filter state"""
        q = ComposedQuery()
        for state in self._state.values():
            if len(state.filters) == 1:
                query_filter = state.filters[0]() #make IQueryFilter object
                q += query_filter #add filter to composed query
            else:
                for spec in state.filters:
                    query_filter = spec()
                    query_filter.conjunction = state.conjunction #AND/OR
                    q += query_filter
        return q
    
    def _facet_query(self):
        return dict([(k.replace('facet.',''),v) for k,v in
            self.request.items() if k.startswith('facet.')])
    
    def applied_filters(self):
        return self._state.values() #list of FacetState objects
    
    def applied_text(self):
        """get text for full text filter value, or return empty string"""
        if 'text' in self._state:
            state = self._state['text']
            return str(state.filters[0].value)
        return ''
    
    def _conjunction_query(self):
        if not hasattr(self, '_conjunction'):
            self._conjunction = dict([(k.replace(
                'conjunction.',''),v) for k,v in
                self.request.items() if k.startswith('conjunction.')])
        return self._conjunction
    
    def get_conjunction(self, facet_name):
        v = self._conjunction_query().get(facet_name, None)
        if v:
            return v.strip().upper()
        return 'OR' #TODO: make this obey form vars from request for AND/OR
    
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
                    self._state[facet_name] = FacetState(facet, (filter_spec,))
                    continue
                vocabulary = facet(self.context)
                if isinstance(filter_name, list):
                    #list of multiple filter name values
                    specs = tuple([vocabulary.getTerm(v) for v in filter_name])
                    state = FacetState(facet, specs)
                    state.conjunction = self.get_conjunction(facet_name)
                    self._state[facet_name] = state
                if filter_name in vocabulary:
                    filter_spec = vocabulary.getTerm(filter_name)
                    self._state[facet_name] = FacetState(facet, (filter_spec,))
                elif str(filter_name) in vocabulary.by_token:
                    filter_spec = vocabulary.getTermByToken(str(filter_name))
                    self._state[facet_name] = FacetState(facet, (filter_spec,))
    
    def facet_state_querystring(self):
        """make base querystring from current facet state"""
        query = {}
        for state in self._state.values():
            k = 'facet.%s' % state.name
            v = []
            for spec in state.filters:
                v.append(spec.name or str(spec.value))
            query[k] = v
        return urllib.urlencode(query, doseq=True)
    
    def include_link(self):
        """link to include subfolders"""
        return 'facet_listing?%s&include_subfolders' % \
            self.facet_state_querystring()
    
    def exclude_link(self):
        """link to exclude subfolders"""
        qs = self.facet_state_querystring()
        return 'facet_listing?%s' % qs.replace('&include_subfolders','')
    
    def _link_fragment(self, facet, filter):
        return urllib.urlencode({('facet.%s' % facet.name) : filter.name})
    
    def filter_link(self, facet, filter):
        """
        Make URL for the intersection of current facet state and a filter
        returning a complete filter link for facet+filter.
        """
        base = self.facet_state_querystring()
        if ('facet.%s' % facet.name) in base:
            for previous_filter in self._state[facet.name].filters:
                base = self.strike_filter(facet, previous_filter, qs=base)
        qs = self._link_fragment(facet,filter)
        if base:
            qs = '%s&%s' % (base, qs)
        if self.include_subfolders:
            qs = '%s&include_subfolders' % qs
        return 'facet_listing?%s' % qs
    
    def strike_filter(self, facet, filter, qs=None):
        """
        Make a URL that includes all filter state in query string EXCEPT
        the facet/filter combination passed, with the effect returning a
        link that removes the filter.
        """
        if qs is None:
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
        if self.include_subfolders:
            qs = '%s&include_subfolders' % qs
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

