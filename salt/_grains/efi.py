# Copyright (c) 2019 SUSE LINUX GmbH, Nuernberg, Germany.

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

import glob
import os.path


def __secure_boot():
    '''Detect if secure-boot is enabled.'''
    enabled = False
    sboot = glob.glob('/sys/firmware/efi/vars/SecureBoot-*/data')
    if len(sboot) == 1:
        enabled = open(sboot[0], 'rb').read()[-1:] == b'\x01'
    return enabled


def uefi():
    '''Populate UEFI grains.'''
    grains = {
        'efi': os.path.exists('/sys/firmware/efi/systab'),
        'efi-secure-boot': __secure_boot(),
    }

    return grains
