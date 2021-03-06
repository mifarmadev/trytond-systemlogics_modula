# This file is part of the systemlogics_modula module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import doctest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import doctest_teardown, doctest_checker


class SystemlogicsModulaTestCase(ModuleTestCase):
    'Test Systemlogics Modula module'
    module = 'systemlogics_modula'


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            SystemlogicsModulaTestCase))
    suite.addTests(doctest.DocFileSuite('scenario_systemlogics_modula.rst',
            tearDown=doctest_teardown, encoding='utf-8',
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE,
            checker=doctest_checker))
    return suite
