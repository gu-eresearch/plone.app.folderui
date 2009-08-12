# -*- coding: utf-8 -*-
#
# GNU General Public License (GPL)
#
__author__ = """Carsten Senger <senger@rehfisch.de>"""
__docformat__ = 'plaintext'

import os
from datetime import date, timedelta
import logging
from random import choice

from Products.CMFCore.utils import getToolByName

from interfaces import ISetCacheTools
from cache import PersistentSetCacheTools
from utils import sitemanager_for


logger = logging.getLogger('folderui')

YEARS = range(1998, 2008)
MONTH = range (1,13)
DAYS = range(1,27) #could be february
DELTA_RANGE = range(20)

#LIMIT = 10 # for faster testing
LIMIT = False # for real

def random_dates():
    '''return two dates within a short range in isoformat and
    chronological order'''
    start = date(choice(YEARS),
                      choice(MONTH),
                      choice(DAYS),)
    end = start + timedelta(choice(DELTA_RANGE))
    return start.isoformat(), end.isoformat()
                      
def create_item(container, item, _type):
    '''create and populate an item with a given type'''
    container.invokeFactory(_type, item['id'], title=item['title'])
    content = container[item['id']]
    content.setDescription(item['description'])
    content.setText(item['text'])
    content.setSubject( '\n'.join(item['categories']) )
    return content

def create_doc(container, item):
    return create_item(container, item,_type='Document')

def create_news(container, item):
    return create_item(container, item, _type='News Item')

def create_event(container, item):
    event = create_item(container, item, _type='Event')

    location = item['country']
    start, end = random_dates()
    event.edit(start_date = start,
               end_date = end,
               location = location)
    return event

def random_create(site, item):
    '''create an item of a random type'''
    factory = choice([create_event, create_news, create_doc])
    content = factory(site[item['foldername']], item)
    logger.info('created item %s, type: %s' % (content.id, content.portal_type))
    return content

def get_samples(context):
    """load all samples and return folders (list) and samples [list of dicts]"""

    # to create ids
    _id = "nobel%s"
    _idnum = 1

    # to collect a unique list of folder names
    folders = {}
    
    CATEGORIES = ('gender', 'prize')

    
    items = []

    # initialize first item
    def new_item():
        '''for convenience'''
        return dict(id = '', title = u'', categories=[],
                    description=u'', text=u'', year='',
                    foldername='', country='')
    item = new_item()

    for line in context.readDataFile('nobel.txt').split('\n'):
        if line.strip():
            name, values = line.split(':', 1)
            values = unicode(values.strip(), encoding='iso-8859-1')

            # categories
            if name in CATEGORIES:
                item['categories'].append(values)
            elif name == 'year':
                item['year'] = values
                decade = values[:3] + '0s'
                item['categories'].append(decade)

            # title
            elif name == 'name':
                item['title'] = values

            # description
            if name in ('longname', 'prize', 'year', 'affiliation'):
                item['description'] = (item['description'] + ' ' + values).strip()

            # everything is text
            item['text'] = item['text'] + ' ' + values

            # use the prize as the foldername
            if name == 'prize':
                foldername = str(values)
                item['foldername'] = foldername
                folders[foldername] = '_'

            # country to use in events
            if name == 'country':
                item['country'] = values
                
        else:
            # we can break if we test this script
            if LIMIT and LIMIT < _idnum:
                break

            # multible newlines might create empty items
            if item == new_item():
                continue

            # compute an id for the object
            item['id'] = _id % _idnum
            _idnum = _idnum + 1

            # save away and get an empty item for the next loop
            items.append(item)
            item = new_item()

    return folders.keys(), items
    
def isNotThisProfile(context):
    return context.readDataFile("plone.app.folderui-samples.txt") is None

def setup_sample_content(context):
    '''set up folders and content'''
    
    if isNotThisProfile(context): return

    site = context.getSite()
    wft = getToolByName(site, 'portal_workflow')
    catalog = getToolByName(site, 'portal_catalog')

    foldernames, items = get_samples(context)

    # create folders
    # warning: we remove existing folders with names we want to use!
    for foldername in foldernames:
        if foldername in site.contentIds():
            site.manage_delObjects( [foldername] )
            logger.info('removed folder %s' % foldername)

        site.invokeFactory('Folder', foldername, title=foldername)
        
        wft.doActionFor(site[foldername], 'publish')
        site[foldername].reindexObject()
        logger.info('created folder %s' % foldername)

    # refresh the catalog to remove deleted items.
    catalog.refreshCatalog(clear=1)

    # create the items
    for item in items:
        content = random_create(site, item)

        # maybe publish it
        if choice((True, False)):
            wft.doActionFor(content, 'publish')
            
        content.reindexObject()
    
    site.reindexObject()


# handler for bootstrapping local set cache component:

def bootstrap_cache_utilities(context=None):
    site = None
    if context is not None and hasattr(context, 'getSite'):
        site = context.getSite()
    else:
        site = context
    sm = sitemanager_for(site)
    if sm.queryUtility(ISetCacheTools) is None:
        logger.info('added persistent local utility for ISetCacheTools')
        sm.registerUtility(PersistentSetCacheTools(), ISetCacheTools)


def modify_ftis(context):
    site = context.getSite()
    typestool = getToolByName(site, 'portal_types')
    modify_ftis = (typestool['Folder'], typestool['Plone Site'])
    for fti in modify_ftis:
        if 'facet_listing' not in fti.view_methods:
            fti.view_methods = fti.view_methods + ('facet_listing',)

