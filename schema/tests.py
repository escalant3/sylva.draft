import unittest

from sylva.spidertests import BaseSpiderTests, OptimizedSpiderSuite
  
class MyBaseSpiderTests(BaseSpiderTests):
    urls_file = 'schema/urls.ini'
    fixtures = ['spider_tests']

def suite():
    return unittest.TestSuite((
        unittest.makeSuite(MyBaseSpiderTests, suiteClass=OptimizedSpiderSuite),
        ))
