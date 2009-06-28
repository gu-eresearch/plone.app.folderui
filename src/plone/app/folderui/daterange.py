from zope.interface import implements
from zope.schema import getFieldsInOrder
from zope.schema.fieldproperty import FieldProperty
from zope.datetime import parseDatetimetz as parseiso
from zope.component import getGlobalSiteManager, IFactory, queryUtility
from calendar import monthrange
from datetime import datetime, timedelta
from interfaces import IDateRange, IDateRangeFactory
from utils import dottedname


## date generation (assume granularity of 1 minute):
month_start = lambda dt: datetime(dt.year, dt.month, 1)
last_monthday = lambda dt: monthrange(dt.year, dt.month)[1]
month_end = lambda dt: datetime(dt.year, dt.month, last_monthday(dt), 23, 59)
year_start = lambda dt: datetime(dt.year, 1, 1, 0, 0)
year_end = lambda dt: datetime(dt.year, 12, 31, 23, 59)
## assume calendar week starts on a Sunday, ends on Saturday
SUNDAY = 6
MONDAY = 0
WEEK_START = SUNDAY #should be configurable in per-site settings
weekday_shift = { SUNDAY:1, MONDAY:0 }[WEEK_START]
week_end_offset = lambda dt: 6 - ((dt.weekday() + weekday_shift) % 7)
week_start_offset = lambda dt: abs(0 - ((dt.weekday() + weekday_shift) % 7))
dwend = lambda dt: (dt + timedelta(days=week_end_offset(dt))).date()
dwstart = lambda dt: (dt - timedelta(days=week_start_offset(dt))).date()
week_end = lambda dt: datetime(*(list(dwend(dt).timetuple()[0:3])+[23,59]))
week_start = lambda dt: datetime(*(list(dwstart(dt).timetuple()[0:3])+[0,0]))

dn_before = lambda dt,n: (dt - timedelta(days=n)).date()
dn_after = lambda dt,n: (dt - timedelta(days=n)).date()
days_before = lambda dt,n: datetime(*(list(dn_before(dt,n).timetuple())))
days_after = lambda dt,n: datetime(*(list(dn_after(dt,n).timetuple())+[23,59]))


class DateRange(object):
    """Date range description object"""
    
    implements(IDateRange)
    
    for _fieldname, _field in getFieldsInOrder(IDateRange):
        locals()[_fieldname] = FieldProperty(_field)
    
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end
    
    @property
    def query_range(self):
        if self.start:
            if self.end:
                return 'minmax'
            return 'min'
        if self.end:
            return 'max'
        return None


class DateRangeFactory(object):
    """relative date range factory"""
    
    implements(IDateRangeFactory)
    
    for _fieldname, _field in getFieldsInOrder(IDateRangeFactory):
        locals()[_fieldname] = FieldProperty(_field)
    
    def __init__(self, startfn=None, endfn=None):
        self.start_function = startfn
        self.end_function = endfn
    
    def __call__(self, dt):
        fstart = self.start_function or (lambda v: None)
        fend = self.end_function or (lambda v: None)
        factory = queryUtility(IFactory, dottedname(IDateRange)) or DateRange
        return factory(fstart(dt), fend(dt))


RANGES = {
    'This month'    : DateRangeFactory(month_start, month_end),
    'Past'          : DateRangeFactory(None, lambda v: v), # up to current
}


gsm = getGlobalSiteManager()
gsm.registerUtility(DateRange, IFactory, name=dottedname(IDateRange))
for name, factory in RANGES.items():
    gsm.registerUtility(factory, IDateRangeFactory, name=name)

