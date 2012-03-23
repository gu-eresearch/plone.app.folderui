from zope.component import getUtility, getUtilitiesFor
from plone.app.folderui.interfaces import IFacetSpecificationFactory, IFacetSettings
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
# plone.app.registry tools for folderui settings

# parse registry settings
# order of facets.... by number, and title..
# facet type ... (vocabulary of factory)
# facet values ... depends on facet type.

# form actions:
#  add (new add form)
#  remove (delete settings)
#  edit (edit form)
#  ordering should be done here? (not necessary).


def parse_facet_settings(registry):
    '''
    plone.app.folderui.facet.<id/num>.<prop>
    '''
    result = {}
    prefix = 'plone.app.folderui'
    for record in registry.records:
        if not record.startswith(prefix):
            continue
        parts = record.split('.')
        current = result
        for x in parts[3:-1]:
            # if name not there create it
            if not x in current:
                current[x] = {}
            current = current[x]
        # store value
        rec = registry.records[record]
        current[parts[-1]] = rec.value
        # TODO: storing it once should be enough
        current['interfaceName'] = rec.interfaceName
    return result


def update_facet_setting(registry, facet_config):
    # TODO: maybe do some check whether a value has been changed and return
    #       some sort of changeset dictionary?
    prefix = 'plone.app.folderui.facet.%s.' % facet_config.pop('name')
    for key, value in facet_config.items():
        record = prefix + key
        if not record in registry.records:
            #ignore non existent records
            continue
        registry.records[record].value = value


def remove_facet_setting(registry, facet_config):
    prefix = 'plone.app.folderui.facet.%s.' % facet_config.pop('name')
    records_to_del = []
    for record in registry.records:
        if not record.startswith(prefix):
            continue
        records_to_del.append(record)
    for name in records_to_del:
        del registry.records[name]


def create_facets(registry):
    config = parse_facet_settings(registry)
    facets = []
    if not 'facet' in config:
        return facets
    for facet_config in sorted(config['facet'].values(), key=lambda item: item['order']):
        # key is the facet id.
        enabled = facet_config.pop('enabled')
        facettype = facet_config.pop('interfaceName')
        factory = getUtility(IFacetSpecificationFactory, name=facettype)
        facet = factory(**facet_config)
        facet.enabled = enabled
        facets.append(facet)
    return facets


def facet_type_vocabulary():
    """
    returns a vocabulary with readable names and values are interface identifiers.
    """
    terms = [SimpleTerm('plone.app.folderui.interfaces.ICatalogFilterConfig',
                        'plone.app.folderui.interfaces.ICatalogFilterConfig',
                        u'Catalog Facet'),
            SimpleTerm('plone.app.folderui.interfaces.IDateRangeConfig',
                        'plone.app.folderui.interfaces.IDateRangeConfig',
                        u'Date Range Facet'),
            SimpleTerm('plone.app.folderui.interfaces.ISparqlFilterConfig',
                        'plone.app.folderui.interfaces.ISparqlFilterConfig',
                        u'Sparql Facet'),
    ]
    return SimpleVocabulary(terms)

    # values = []
    # for name, _ in getUtilitiesFor(IFacetSpecificationFactory):
    #     values.append[name]
    # return SimpleVocabulary.fromValues(values)


def record_change_handler(event):
    if event.record.__name__.startswith('plone.app.folderui.facet.'):
        getUtility(IFacetSettings).clear()
