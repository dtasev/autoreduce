# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Test ICAT prefix mapping
"""
import unittest
from unittest.mock import patch

from utils.clients.tools.isisicat_prefix_mapping import get_icat_instrument_prefix


# pylint:disable=no-self-use,too-few-public-methods,too-many-public-methods
class MockInstrumentQueryResult:
    """
    Mocks result of isisicat_prefix_mapping.client.execute_query for an instrument
    """

    def __init__(self, name, full_name):
        self.name = name
        # camelCase used due to mocking of external class
        self.fullName = full_name  # pylint:disable=invalid-name


class TestICATPrefixMapping(unittest.TestCase):
    """
    Test ICAT prefix mapping
    """
    DIR = "utils.clients.tools.isisicat_prefix_mapping"

    @patch('icat.Client.__init__', return_value=None)
    @patch(f"{DIR}.AUTOREDUCTION_INSTRUMENT_NAMES", ['ENGINGX'])
    @patch('utils.clients.icat_client.ICATClient.execute_query')
    def test_get_icat_instrument_prefix_executes_icat_query(self, mock_execute_query, _):
        """
        Test: If instruments are fetched through a query
        When: Testing if get_icat_instrument_prefix executes an ICAT query
        """
        get_icat_instrument_prefix()
        mock_execute_query.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch(f"{DIR}.AUTOREDUCTION_INSTRUMENT_NAMES", ['INVALIDINSTUMENT'])
    @patch('logging.Logger.warning')
    @patch('utils.clients.icat_client.ICATClient.execute_query')
    def test_get_icat_instrument_prefix_log_invalid_instrument(self, _mock_execute_query,
                                                               mock_logger_warning, _):
        """
        Test: If invalid instrument name in utils.settings.VALID_INSTRUMENTS is logged as not found
        When: Testing if get_icat_instrument_prefix picks up invalid instruments
        """
        get_icat_instrument_prefix()
        mock_logger_warning.assert_called_once()

    @patch('icat.Client.__init__', return_value=None)
    @patch(f"{DIR}.AUTOREDUCTION_INSTRUMENT_NAMES", ["ENGINX", "GEM"])
    @patch('utils.clients.icat_client.ICATClient.execute_query',
           return_value=[MockInstrumentQueryResult("ENG", "ENGINX"),
                         MockInstrumentQueryResult("GEM", "GEM")])
    def test_icat_prefix_mapping_length(self, _mock_instruments, _mock_execute_query):
        """
        Test: get_icat_instrument_prefix produces the same number of results as stored in
              utils.settings.VALID_INSTRUMENTS
        When: Called when testing to see if the correct number of instruments in prefix mapping
        """
        actual = get_icat_instrument_prefix()
        self.assertEqual(2, len(actual.keys()))

    @patch('icat.Client.__init__', return_value=None)
    @patch('utils.clients.icat_client.ICATClient.execute_query')
    @patch(f"{DIR}.AUTOREDUCTION_INSTRUMENT_NAMES", ["ENGINX"])
    def test_get_icat_instrument_prefix_without_argument(self, mock_execute_query, _):
        """
        Test: If get_icat_instrument_prefix properly maps instrument names map to ICAT
              instrument prefixes using utils.settings.VALID_INSTRUMENTS
        When: Called when testing correct mapping
        """
        expected = ("ENG", "ENGINX")
        mock_execute_query.return_value = [MockInstrumentQueryResult(*expected)]

        actual = get_icat_instrument_prefix()
        self.assertEqual(expected[0], actual[expected[1]])

    @patch('icat.Client.__init__', return_value=None)
    @patch('utils.clients.icat_client.ICATClient.execute_query')
    def test_get_icat_instrument_prefix_with_argument(self, mock_execute_query, _):
        """
        Test: If get_icat_instrument_prefix properly maps instrument names map to ICAT
              instrument prefixes using a passed in list of instruments to check
        When: Called when testing correct mapping using passed in list
        """
        expected = ("ENG", "ENGINX")
        mock_execute_query.return_value = [MockInstrumentQueryResult(*expected)]

        actual = get_icat_instrument_prefix([expected[1]])
        self.assertEqual(expected[0], actual[expected[1]])
