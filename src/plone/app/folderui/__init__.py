from Products.CMFCore.DirectoryView import registerDirectory


def initialize(context):
    """Initializer called when used as a Zope 2 product."""

    registerDirectory("skins", globals())
