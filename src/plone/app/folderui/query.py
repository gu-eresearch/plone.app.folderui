from zope.interface import implements, implementer
from zope.schema import getFieldsInOrder
from zope.schema.fieldproperty import FieldProperty
from zope.component import (IFactory, queryAdapter,
    ComponentLookupError, adapter, queryUtility, )
from interfaces import (IQueryFilter, IComposedQuery, IDateRange,
    IDateRangeFactory, ICatalogQueryFilter, IQueryFilterFactory)
from utils import dottedname
from datetime import datetime


class ComposedQuery(object):
    
    implements(IComposedQuery)
    
    for _fieldname, _field in getFieldsInOrder(IComposedQuery):
        locals()[_fieldname] = FieldProperty(_field)
    
    def __init__(self, filters=(), interindex_operator='AND'):
        self.filters = list(filters)
        self.interindex_operator = str(interindex_operator)
    
    def __add__(self, other):
        factory = self.__class__
        new_composition = factory(self.filters, self.interindex_operator) #copy
        if IComposedQuery.providedBy(other):
            new_composition.filters += other.filters
        elif IQueryFilter.providedBy(other):
            new_composition.filters.append(other)
        else:
            raise ValueError('cannot add: other is of unknown component type.')
        return new_composition


class CatalogQueryFilter(object):
    
    implements(ICatalogQueryFilter)
    
    for _fieldname, _field in getFieldsInOrder(IQueryFilter):
        locals()[_fieldname] = FieldProperty(_field)
    
    def __init__(self, index=u'', value=None, query_range=None, neg=False):
        self.index = unicode(index)
        self.value = value
        self.query_range = query_range
        self.negated = bool(neg)
    
    def __add__(self, other):
        default = ComposedQuery
        factory = queryUtility(IFactory, dottedname(IComposedQuery)) or default
        return factory(filters=[self,other])


@adapter(IDateRange)
@implementer(IQueryFilter)
def date_range_filter(dr):
    """
    Note, this will return a Query Filter with no index name, the burden is on
    calling code to set the index attribute of the returned filter.
    
    EXAMPLE USAGE:
    --------------
   
    Register default components declared in ZCML and daterange.py:
   
    >>> from plone.app.folderui.config import register_defaults
    >>> register_defaults()
    >>> import plone.app.folderui.daterange #default date range factories
     
    Get date range factory and date range:
    
    >>> from datetime import datetime
    >>> from zope.component import queryUtility
    >>> from plone.app.folderui.utils import dottedname
    >>> from plone.app.folderui.interfaces import IDateRangeFactory
    >>> this_month_factory = queryUtility(IDateRangeFactory, 'This month')
    >>> this_month = this_month_factory(datetime.now())
    
    Use date range to create query filter:
    
    >>> from plone.app.folderui.interfaces import IQueryFilter
    >>> from plone.app.folderui.query import date_range_filter
    >>> this_month_filter = date_range_filter(this_month)
    >>> assert IQueryFilter.providedBy(this_month_filter)
    
    date_range_filter() can also adapt IDateRangeFactory, though this is not
    advertised in function decorators; here is another date range filter from
    a factory, relative to datetime.now():
    
    >>> past_factory = queryUtility(IDateRangeFactory, 'Past')
    >>> past_filter = date_range_filter(past_factory)
    
    Create a composed query from two date ranges:
    >>> composed_query = past_filter + this_month_filter
    >>> from plone.app.folderui.interfaces import IComposedQuery
    >>> assert IComposedQuery.providedBy(composed_query)
    >>> assert past_filter in composed_query.filters
    >>> assert this_month_filter in composed_query.filters
    
    """
    assert IDateRange.providedBy(dr) or IDateRangeFactory.providedBy(dr)
    if IDateRangeFactory.providedBy(dr):
        dr = dr(datetime.now())
    factory = queryAdapter(dr, IQueryFilterFactory)
    if factory is None:
        return ComponentLookupError('cannot find factory for query filter')
    return factory(value=(dr.start, dr.end), query_range=dr.query_range)
