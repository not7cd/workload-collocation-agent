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


# Building owca.
FROM centos:7 AS owca

#RUN yum -y update
RUN yum -y install epel-release
RUN yum -y install python36 python-pip which make git

RUN pip install pipenv

#COPY . .
RUN git clone https://github.com/intel/owca.git
WORKDIR /owca

RUN pipenv install --dev
#--system --ignore-pipfile --deploy
RUN pipenv run make owca_package

# Builing final container that consists of owca only.
FROM centos:7

ENV CONFIG=/etc/owca/owca_config.yml \
    LOG=info \
    EXTRA_COMPONENT=example.external_package:ExampleDetector

RUN yum install -y epel-release
RUN yum install -y python36

COPY --from=owca /owca/dist/owca.pex /usr/bin/

#USER owca

ENTRYPOINT \
    python36 /usr/bin/owca.pex \
        --config $CONFIG \
        --register $EXTRA_COMPONENT \
        --log $LOG \
        -0 \
    && /bin/bash
