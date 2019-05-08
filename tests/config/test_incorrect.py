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


from io import StringIO

from wca import config

import pytest

foo_yaml = """
x: !FooNeverRegistered
"""


def test_config_unknown_tag():

    with pytest.raises(config.ConfigLoadError,
                       match="could not determine a constructor for the tag '!FooNeverRegistered'."
                             "*Available tags are: "):
        config._parse(StringIO(foo_yaml))


bar_yaml = """
b: !Bar
    y: 5
"""


@config.register
class Bar:

    def __init__(self, x: int):
        pass


def test_config_incorrect_constructor():
    with pytest.raises(config.ConfigLoadError, match="Cannot instantiate 'Bar'"):
        config._parse(StringIO(bar_yaml))
