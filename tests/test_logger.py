# Copyright (c) 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import pytest

from wca.logger import configure_loggers_from_dict, parse_loggers_from_list

from unittest.mock import patch


@pytest.mark.parametrize('log_levels_list,expected_log_levels_dict', (
    ([], {}),
    (['DEBUG'], {'wca': 'DEBUG'}),
    (['DEBUG', 'foo.bar:info'], {'wca': 'DEBUG', 'foo.bar': 'info'}),
))
def test_parsing_cmdline(log_levels_list, expected_log_levels_dict):
    log_levels_dict = parse_loggers_from_list(log_levels_list)
    assert log_levels_dict == expected_log_levels_dict


@patch('wca.logger.init_logging')
def test_configuring_loggers(init_logging_mock):
    configure_loggers_from_dict({'foo': 'debug'})
    init_logging_mock.assert_called_once_with('debug', package_name='foo')
