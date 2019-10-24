#! /bin/bash

#
# Author: Alberto Planas <aplanas@suse.com>
#
# Copyright 2019 SUSE LLC.
#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# Setup the environment so the Python modules living in salt/_* can be
# found.

cd "$(dirname "${BASH_SOURCE[0]}")"

test_env=$(mktemp -d -t tmp.XXXX)
tear_down() {
    rm -fr "$test_env"
}

trap tear_down EXIT

# Create the temporary Python modules, that once added in the
# PYTHON_PATH can be found and imported
touch "$test_env"/__init__.py
for module in modules states grains utils; do
    mkdir "$test_env"/"$module"
    touch "$test_env"/"$module"/__init__.py
    [ "$(ls -A ../salt/_"$module")" ] && ln -sr ../salt/_"$module"/* "$test_env"/"$module"/
done

if [ -z $PYTHONPATH ]; then
    export PYTHONPATH="$test_env":"$test_env"/utils:.
else
    export PYTHONPATH="$PATHONPATH":"$test_env":"$test_env"/utils:.
fi

if [ -z "$*" ]; then
    python3 -m unittest discover
else
    python3 -m unittest "$@"
fi
