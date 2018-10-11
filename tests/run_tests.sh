#! /bin/bash

# Copyright (c) 2018 SUSE LINUX GmbH, Nuernberg, Germany.

# This file is part of Salt-autoinstaller.

# Salt-autoinstaller is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Salt-autoinstaller is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Salt-autoinstaller.  If not, see <https://www.gnu.org/licenses/>.

# Setup the environment so the Python modules living in salt/_modules
# and salt/_states can be found.

test_env=$(mktemp -d -t tmp.XXXX)
tear_down() {
    rm -fr "$test_env"
}

trap tear_down EXIT

# Create the temporal Python modules, that once added in the
# PYTHON_PATH can be found and imported
touch "$test_env"/__init__.py
for module in modules states; do
    mkdir "$test_env"/"$module"
    touch "$test_env"/"$module"/__init__.py
    [ "$(ls -A ../salt/_"$module")" ] && ln -sr ../salt/_"$module"/* "$test_env"/"$module"/
done

if [ -z $PYTHONPATH ]; then
    export PYTHONPATH="$test_env":.
else
    export PYTHONPATH="$PATHONPATH":"$test_env":.
fi

if [ -z "$*" ]; then
    python3 -m unittest discover
else
    python3 -m unittest "$@"
fi
