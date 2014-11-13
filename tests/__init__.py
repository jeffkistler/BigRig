import unittest

from .scanner import TestScanner
from .parser import TestParser

def test_suite():
    scanner_suite = unittest.makeSuite(TestScanner)
    parser_suite = unittest.makeSuite(TestParser)
    return unittest.TestSuite([scanner_suite, parser_suite])

if __name__ == "__main__":
    suite = test_suite()
    unittest.TextTestRunner(verbosity=2).run(suite)
