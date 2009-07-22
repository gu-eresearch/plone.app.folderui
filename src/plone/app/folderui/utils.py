from Products.CMFCore.utils import getToolByName
from zope.component import queryUtility, getSiteManager, getGlobalSiteManager

from interfaces import ISetCacheTools


dottedname = lambda o: '%s.%s' % (o.__module__, o.__name__)


def rid_for_object(catalog, obj):
    r = catalog(getId=obj.id)
    if not r:
        return None
    return r[0].getRID()


def modify_handler(obj, event):
    """
    modified/created content needs to invalidate facet listings, in this
    case, the rid of the object is added to a queue, and should later
    be removed after faceted navigation removes.
    """
    catalog = getToolByName(obj, 'portal_catalog')
    while 1:
        rid = rid_for_object(catalog, obj)
        if rid is None:
            # should only happen on document creation; side-effect might be 
            # duplicative calls to reindexObject if another handler 
            # or code calls...
            obj.reindexObject()
            continue
        break
    set_cache_tools = queryUtility(ISetCacheTools)
    if set_cache_tools is not None:
        if rid not in set_cache_tools.invalidated_records:
            set_cache_tools.invalidated_records.insert(rid)



def sitemanager_for(site):
    print site
    if site is not None:
        portal = getToolByName(site, 'portal_url').getPortalObject()
        return getSiteManager(portal)
    return getGlobalSiteManager()

