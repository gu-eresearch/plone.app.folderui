from Products.Five import BrowserView
from plone.app.folderui.defaults import FACETS
from plone.app.folderui.query import ComposedQuery
from plone.app.folderui.catalog import AdvancedQueryRunner


class FacetViewInfo(object):
    """object containing render-ready facet info"""
    def __init__(self, title, spec, filters):
        self.title = title
        self.spec = spec
        self.filters = filters


class FacetListing(BrowserView):
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @property
    def facets(self):
        result = []
        for k,v in FACETS.items():
            filters = v(self.context) #call to get filter vocab
            result.append(FacetViewInfo(k,v,filters))
        return result
    
    def listings(self, **kwargs):
        q = ComposedQuery()
        runner = AdvancedQueryRunner(self.context)
        #runner = queryUtility(IQueryRunner) #TODO: decouple later
        result_map = runner(q)
        return result_map.values() #LazyMap of brains

