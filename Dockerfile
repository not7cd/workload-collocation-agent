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

RUN yum -y update
RUN yum -y install yum-utils
RUN yum -y groupinstall development
RUN yum -y install https://centos7.iuscommunity.org/ius-release.rpm
RUN yum makecache
RUN yum -y install python35 python-pip
#RUN yum install -y centos-release-scl epel-release makecache python35-setuptools

RUN pip install pipenv

WORKDIR /owca

COPY . .

RUN pipenv install --dev
RUN pipenv run make owca_package

# Builing final container that consists of owca only.
FROM centos:7

RUN yum install -y epel-release python36 makecache

# Copy owca binary and its configuration.
COPY --from=rpc-perf /owca/dist/owca.pex /usr/bin/
# Prepare directory for owca configuration
RUN mkdir /etc/owca
# Create owca group to enable running OWCA as non-root
#RUN groupadd owca
# Create owca user to enable running OWCA as non-root
USER owca

#  Set "0" as content of perf_event_paranoid to enable running OWCA as non-root
RUN sudo sh -c 'echo 0 >/proc/sys/kernel/perf_event_paranoid'

# Changing ownership of mon_groups enables creating mon_groups by non-root user
RUN sudo chown -R owca:owca /sys/fs/resctrl/mon_groups

COPY config.yml.j2 /etc/owca/owca_config.yml

RUN mkdir /var/lib/owca && sudo chown -R owca:owca /var/lib/owca

# Prepare service under systemd.
COPY owca.service.j2 /etc/systemd/system/owca.service
# Reload systemd and restart owca service
RUN sudo systemd reload owca



