from zope.interface import Interface
from zope.schema import TextLine, Tuple, Object, Choice

from plone.app.folderui.interfaces import (IFacetSpecification,
    IFilterSpecification, mkvocab)


class IFacetState(Interface):
    """given query state for a single given facet"""
    
    name = TextLine(
        title=u'Facet name',
        description=u'Name of facet',
        readonly=True, #property computed from facet.name
        )
    
    facet = Object(
        title=u'Facet specification',
        schema=IFacetSpecification,
        required=True,)
    
    filters = Tuple(
        title=u'Applied filter specifications',
        value_type=Object(schema=IFilterSpecification),
        constraint=lambda v: len(v)>0, #non-empty tuple
        )
    
    conjunction = Choice(vocabulary=mkvocab(('AND','OR')), default='OR')
