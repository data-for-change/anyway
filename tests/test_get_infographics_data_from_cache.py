import unittest
from unittest import TestCase
from unittest.mock import Mock, patch
from anyway.infographics_utils import get_infographics_data
import anyway.parsers.infographics_data_cache_updater


class Test_get_infographics_data_from_cache(TestCase):
    def test_get_not_existing_from_cache(self):
        cache_data = anyway.parsers.infographics_data_cache_updater\
            .get_infographics_data_from_cache(17, 1)
        self.assertEqual(cache_data, {}, 'returned value from cache should be None')

    @patch('anyway.infographics_utils.infographics_data_cache_updater')
    def test_get_existing(self, get_from_cache):
        expected = {'data': 'data'}
        get_from_cache.get_infographics_data_from_cache.return_value = expected
        create_mock_infographics_data = Mock()
        res = get_infographics_data(7, 1)
        get_from_cache.get_infographics_data_from_cache.assert_called_with(7, 1)
        get_from_cache.create_mock_infographics_data.assert_not_called()
        create_mock_infographics_data.assert_not_called()
        self.assertEqual(res, expected, f'{expected} should be found in cache')


    @patch('anyway.infographics_utils.create_mock_infographics_data')
    @patch('anyway.infographics_utils.infographics_data_cache_updater')
    def test_get_not_existing(self, get_from_cache, utils):
        expected = {'data': "created"}
        get_from_cache.get_infographics_data_from_cache.return_value = {}
        utils.return_value = expected
        # create_infographics_data = Mock()
        res = get_infographics_data(7, 1)
        get_from_cache.get_infographics_data_from_cache.assert_called_with(7, 1)
        utils.assert_called_with(7, 1)
        self.assertEqual(res, expected, f'{expected} should be found in cache')


    @patch('anyway.infographics_utils.create_mock_infographics_data')
    @patch('anyway.infographics_utils.infographics_data_cache_updater')
    def test_get_throws_exception(self, get_from_cache, utils):
        expected = {'data': "created"}
        get_from_cache.get_infographics_data_from_cache.side_effect = RuntimeError
        utils.return_value = expected
        # create_infographics_data = Mock()
        res = get_infographics_data(7, 1)
        get_from_cache.get_infographics_data_from_cache.assert_called_with(7, 1)
        utils.assert_called_with(7, 1)
        self.assertEqual(res, expected, f'{expected} should be found in cache')


if __name__ == '__main__':
    unittest.main()
