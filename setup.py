from setuptools import setup, find_packages
import os

version = '0.03-gurc3'

def read(*rnames):
    '''read files given a sequence of path segments'''
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()


setup(name='plone.app.folderui',
      version=version,
      description="Folder user interface enhancements for Plone.",
      long_description=read('README.txt') + "\n" +
                       read('docs', 'HISTORY.txt'),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Sean Upton',
      author_email='sdupton@gmail.com',
      url='http://dev.plone.org/plone/wiki/Gsoc2009/FolderUiImprovements',
      license='GPL',
      packages=find_packages('src', exclude=['ez_setup']),
      package_dir={'': 'src'},
      namespace_packages=['plone', 'plone.app'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Products.CMFCore',  # need this to run zcml deps too
          'Products.AdvancedQuery',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
