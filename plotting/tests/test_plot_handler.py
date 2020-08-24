# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Tests for the PlotHandler class.
Currently tests:
initialisation of class parameters
construction of regular expression for looking up existing files
calling the SFTPClient with correct parameters
"""
import os
import unittest

from mock import patch, MagicMock, call

from plotting.plot_handler import PlotHandler
from utils.project.structure import get_project_root


# pylint:disable=line-too-long, protected-access
class TestPlotHandler(unittest.TestCase):
    """
    Test all the functionality of the PlotHandler
    """

    # pylint:disable=too-many-instance-attributes
    def setUp(self):
        """
        Create a few test PlotHandler objects
        """
        self.expected_file_extensions = ["png", "jpg", "bmp", "gif", "tiff"]
        self.expected_file_extension_regex = '(png|jpg|bmp|gif|tiff)'
        self.expected_mari_file_regex = f'MAR(I)?1234.*.{self.expected_file_extension_regex}'
        self.expected_wish_file_regex = f"WISH1234.*.{self.expected_file_extension_regex}"
        self.expected_wish_instrument_name = "WISH"
        self.expected_mari_instrument_name = "MARI"
        self.expected_mari_rb_number = 12345678
        self.expected_mari_run_number = 1234
        self.expected_mari_rb_folder = "/instrument/MARI/RBNumber/RB12345678/1234/autoreduced/"
        self.test_plot_handler = PlotHandler(instrument_name=self.expected_mari_instrument_name,
                                             rb_number=self.expected_mari_rb_number,
                                             run_number=self.expected_mari_run_number,
                                             server_dir=self.expected_mari_rb_folder)

        self.expected_static_graph_dir = os.path.join(get_project_root(), 'WebApp',
                                                      'autoreduce_webapp', 'static',
                                                      'graphs')
        self.mock_cache = MagicMock()

    # pylint:disable=unused-argument
    @patch('plotting.plot_handler.PlotHandler._generate_file_name_regex', return_value="pattern")
    def test_init(self, mock_gen_reg):
        """
        Test: Class variables are initiated correctly
        When: PlotHandler is initialised
        """
        # Cannot use handler from setup else we cant patch the mock method
        plot_handler = PlotHandler(self.expected_mari_instrument_name,
                                   self.expected_mari_run_number,
                                   self.expected_mari_rb_folder,
                                   rb_number=self.expected_mari_rb_number)

        self.assertEqual(self.expected_mari_instrument_name, plot_handler.instrument_name)
        self.assertEqual(self.expected_mari_run_number, plot_handler.run_number)
        self.assertEqual(self.expected_mari_rb_folder, plot_handler.server_dir)
        self.assertEqual(self.expected_file_extensions, plot_handler.file_extensions)
        self.assertEqual(self.expected_mari_rb_number, plot_handler.rb_number)
        self.assertEqual(self.expected_static_graph_dir, plot_handler.static_graph_dir)
        self.assertEqual("pattern", plot_handler.file_regex)

    def test_generate_file_name_regex(self):
        """
        Test: Check that the correct regular expression for file look-up is created
        When: Valid instrument names are supplied to _generate_file_name_regex
        """
        actual = self.test_plot_handler._generate_file_name_regex()
        self.assertEqual(self.expected_mari_file_regex, actual)
        self.test_plot_handler.instrument_name = self.expected_wish_instrument_name
        actual = self.test_plot_handler._generate_file_name_regex()
        self.assertEqual(self.expected_wish_file_regex, actual)

    def test_generate_file_extension_regex(self):
        """
        Test: Correct file extension pattern is generated
        When: _generate_file_extension_pattern() is called
        """
        expected_pattern = '(png|jpg|bmp|gif|tiff)'
        actual_pattern = self.test_plot_handler._generate_file_extension_regex()
        self.assertEqual(expected_pattern, actual_pattern)

        self.test_plot_handler.file_extensions.append('txt')
        expected_pattern = '(png|jpg|bmp|gif|tiff|txt)'
        actual_pattern = self.test_plot_handler._generate_file_extension_regex()
        self.assertEqual(expected_pattern, actual_pattern)

    def test_generate_file_name_regex_invalid(self):
        """
        Test: Assert None is returned
        When: calling _generate_file_name_regex with invalid instrument
        """
        self.test_plot_handler.instrument_name = "Not instrument"
        self.assertIsNone(self.test_plot_handler._generate_file_name_regex())

    @patch('plotting.plot_handler.PlotHandler._get_plot_files_locally', return_value=[])
    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files', return_value=["file1", "file2"])
    @patch('plotting.plot_handler.PlotHandler._get_plot_files_remotely', return_value=["file1", "file2"])
    def test_get_plot_files_file_exists_remotely_only(self, mock_get_remote, mock_check_remote, mock_get_locally):
        """
        Test: Plot file is obtained remotely
        When: no plot exists in cache
        """
        self.assertEqual(mock_check_remote.return_value, self.test_plot_handler.get_plot_file())
        mock_get_locally.assert_called_once()
        mock_check_remote.assert_called_once()
        mock_get_remote.assert_called_once()

    @patch('plotting.plot_handler.PlotHandler._get_plot_files_locally', return_value=["file1", "file2"])
    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files')
    @patch('plotting.plot_handler.PlotHandler._get_plot_files_remotely')
    def test_get_plot_files_file_exists_locally(self, mock_get_remote, mock_check_remote, mock_get_locally):
        """
        Test: Plot file is obtained from local storage
        When: Plot exists in cache
        """
        self.assertEqual(mock_get_locally.return_value, self.test_plot_handler.get_plot_file())
        mock_get_locally.assert_called_once()
        mock_get_remote.assert_not_called()
        mock_check_remote.assert_not_called()

    @patch('plotting.plot_handler.PlotHandler._get_plot_files_locally', return_value=[])
    @patch('plotting.plot_handler.PlotHandler._check_for_plot_files', return_value=[])
    @patch('plotting.plot_handler.PlotHandler._get_plot_files_remotely', return_value=[])
    def test_get_plot_files_none_remote_none_locally(self, mock_get_remote, mock_check_remote, mock_get_locally):
        """
        Test: empty list is returned
        When: no file exists locally or remotely
        """
        self.assertEqual([], self.test_plot_handler.get_plot_file())
        mock_check_remote.assert_called_once()
        mock_get_locally.assert_called_once()
        mock_get_remote.assert_called_once()

    @patch('plotting.plot_handler.SFTPClient')
    def test__check_for_plot_files_no_files(self, mock_sftp_client):
        """
        Test: Empty list returned
        When: No files exist remotely
        """
        client_mock_instance = mock_sftp_client.return_value
        client_mock_instance.get_filenames.return_value = []

        result = self.test_plot_handler._check_for_plot_files()

        client_mock_instance.get_filenames.assert_called_with(server_dir_path=self.expected_mari_rb_folder,
                                                              regex=self.expected_mari_file_regex)

        self.assertEqual([], result)

    @patch('plotting.plot_handler.SFTPClient')
    def test__check_for_plot_files_with_files(self, mock_sftp_client):
        """
        Test: File names are returned
        When: Files exist remotely
        """
        client_mock_instance = mock_sftp_client.return_value
        client_mock_instance.get_filenames.return_value = ["file1", "file2"]

        result = self.test_plot_handler._check_for_plot_files()

        client_mock_instance.get_filenames.assert_called_with(server_dir_path=self.expected_mari_rb_folder,
                                                              regex=self.expected_mari_file_regex)

        self.assertEqual(["file1", "file2"], result)

    @patch('plotting.plot_handler.SFTPClient')
    @patch('os.path.join')
    @patch('plotting.plot_handler.PlotHandler._cache_plots')
    def test__get_plot_files_remotely_no_files_remotely(self, mock_cache_plots, mock_os_join, mock_sftp_client):
        """
        Test: Empty list is returned
        When: when no files are found remotely
        """
        mock_client_instance = mock_sftp_client.return_value

        self.assertEqual([], self.test_plot_handler._get_plot_files_remotely([]))
        mock_os_join.assert_not_called()
        mock_client_instance.assert_not_called()
        mock_cache_plots.assert_not_called()

    @patch('plotting.plot_handler.SFTPClient')
    @patch('os.path.join')
    @patch('plotting.plot_handler.PlotHandler._cache_plots')
    def test__get_plot_files_remotely_returns_all_files(self, mock_cache_plots, mock_os_join, mock_sftp_client):
        """
        Test: All files returned
        When: Files found remotely
        """
        expected = [f'{self.expected_static_graph_dir}/file1',
                    f'{self.expected_static_graph_dir}/file2']
        mock_client_instance = mock_sftp_client.return_value
        mock_os_join.side_effect = expected

        actual = self.test_plot_handler._get_plot_files_remotely(["file1", "file2"])

        self.assertEqual(expected, actual)
        join_calls = [call(self.test_plot_handler.static_graph_dir, 'file1'),
                      call(self.test_plot_handler.static_graph_dir, 'file2')]
        mock_os_join.assert_has_calls(join_calls)
        mock_client_instance.retrieve.assert_called()
        mock_cache_plots.assert_called_with(expected)

    @patch('plotting.plot_handler.SFTPClient')
    @patch('os.path.join')
    @patch('plotting.plot_handler.PlotHandler._cache_plots')
    def test__get_plot_files_remotely_one_plot_not_found(self, mock_cache, mock_join, mock_sftp_client):
        """
        Test: A file is returned
        When: Other file doesnt exist
        """
        expected = [f'{self.expected_static_graph_dir}/file2']
        mock_client_instance = mock_sftp_client.return_value
        mock_join.side_effect = [f'{self.expected_static_graph_dir}/file1',
                                 f'{self.expected_static_graph_dir}/file2']
        mock_client_instance.retrieve.side_effect = [RuntimeError, None]

        actual = self.test_plot_handler._get_plot_files_remotely(['file1', 'file2'])

        self.assertEqual(expected, actual)
        join_calls = [call(self.test_plot_handler.static_graph_dir, 'file1'),
                      call(self.test_plot_handler.static_graph_dir, 'file2')]
        mock_join.assert_has_calls(join_calls)
        mock_client_instance.retrieve.assert_called()
        mock_cache.assert_called_with(expected)
