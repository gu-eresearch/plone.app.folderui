from Products.Five import zcml
import Products.Five
import Products.GenericSetup

import plone.app.folderui


def _bootstrap_zcml_prerequisites():
    zcml.load_config('configure.zcml', Products.Five)
    zcml.load_config('meta.zcml', Products.Five)
    zcml.load_config('meta.zcml', Products.GenericSetup)
    zcml.load_config('configure.zcml', Products.GenericSetup)


def register_defaults():
    _bootstrap_zcml_prerequisites()
    zcml.load_config('configure.zcml', plone.app.folderui)

