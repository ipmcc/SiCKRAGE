#!/usr/bin/env python2
# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import sys

import urllib3.contrib
from distutils.version import LooseVersion


PIP_BOOTSTRAP_URL = "https://bootstrap.pypa.io/get-pip.py"
PIP_MIN_VERSION = "7.1.2"

def install_pip(path, user=False):
    try:
        import pip
        pip_version = LooseVersion(pip.__version__)
    except ImportError:
        pip = None
        pip_version = LooseVersion("0.0.0")

    if pip_version >= LooseVersion(PIP_MIN_VERSION):
        return

    file_name = os.path.join(path, PIP_BOOTSTRAP_URL.split('/')[-1])
    print("Downloading pip ...")
    try:
        import urllib
        urllib.urlretrieve(PIP_BOOTSTRAP_URL, file_name)

        print("Installing pip ...")
        import subprocess
        subprocess.check_call([sys.executable, file_name] + (["--user"] if user else []))
    finally:
        print("Cleaning up downloaded pip files")
        try:
            os.remove(file_name)
        except:
            pass


def install_packages(path, constraints, user=False):
    import pip
    from pip.commands.install import InstallCommand
    from pip.exceptions import InstallationError

    pip_install_cmd = InstallCommand()

    # list installed packages
    try:
        installed = [x.project_name.lower() for x in pip.get_installed_distributions(local_only=True, user_only=user)]
    except:
        installed = []

    # read requirements file
    with open(path) as f:
        packages = [x.strip() for x in f.readlines() if x.strip().lower() not in installed]

    # install requirements packages
    options = pip_install_cmd.parse_args([])[0]
    options.use_user_site = user
    options.constraints = [constraints]
    options.quiet = 1

    for i, pkg_name in enumerate(packages, start=1):
        try:
            print(r"[%3.2f%%]::Installing %s package" % (i * 100 / len(packages), pkg_name))
            pip_install_cmd.run(options, [pkg_name])
        except InstallationError:
            try:
                options.ignore_dependencies = True
                pip_install_cmd.run(options, [pkg_name])
            except:
                continue
        except IndexError:
            continue

    if len(packages) > 0:
        return True


def upgrade_packages(constraints, user=False):
    from pip.commands.list import ListCommand
    from pip.commands.install import InstallCommand
    from pip.exceptions import InstallationError

    packages = []

    pip_install_cmd = InstallCommand()
    pip_list_cmd = ListCommand()


    while True:
        # list packages that need upgrading
        try:
            options = pip_list_cmd.parse_args([])[0]
            options.use_user_site = user
            options.cache_dir = None
            options.outdated = True

            packages = [p.project_name for p, y, _ in pip_list_cmd.find_packages_latest_versions(options)
                        if getattr(p, 'version', 0) != getattr(y, 'public', 0)]
        except:
            packages = []

        # Never upgrade yourself. It doesn't end well. (Any sources already loaded are the old version, anything
        # loaded after this is the new version, it's a mess. It also borks development installs.)
        if "sickrage" in packages:
            packages.remove("sickrage")

        options = pip_install_cmd.parse_args([])[0]
        options.use_user_site = user
        options.constraints = [constraints]
        options.cache_dir = None
        options.upgrade = True
        options.quiet = 1

        for i, pkg_name in enumerate(packages, start=1):
            try:
                print(r"[%3.2f%%]::Upgrading %s package" % (i * 100 / len(packages), pkg_name.lower()))
                pip_install_cmd.run(options, [pkg_name])
            except InstallationError:
                try:
                    options.ignore_dependencies = True
                    pip_install_cmd.run(options, [pkg_name])
                except:continue
            except IndexError:
                continue
        else:
            break

def install_ssl(path, constraints, user=False):
    try:
        print("Installing and Patching SiCKRAGE SSL Contexts")
        # noinspection PyUnresolvedReferences,PyUnresolvedReferences,PyUnresolvedReferences
        import urllib3.contrib.pyopenssl
        urllib3.contrib.pyopenssl.inject_into_urllib3()
        urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST = "MEDIUM"
    except ImportError:
        return install_packages(path, constraints, user)


def install_requirements(path, optional=False, ssl=False, user=False):
    constraints = os.path.abspath(os.path.join(path, 'constraints.txt'))

    # install ssl packages
    if ssl:
        try:
            if install_ssl(os.path.abspath(os.path.join(path, 'ssl.txt')), constraints, user):
                os.execl(sys.executable, sys.executable, *sys.argv)
        except:
            pass

    print("Checking for required SiCKRAGE packages, please stand by ...")
    install_packages(os.path.abspath(os.path.join(path, 'requirements.txt')), constraints, user)

    if optional:
        print("Checking for optional SiCKRAGE packages, please stand by ...")
        try:
            install_packages(os.path.abspath(os.path.join(path, 'optional.txt')), constraints, user)
        except:
            pass

    print("Checking for upgradable SiCKRAGE packages, please stand by ...")
    upgrade_packages(constraints, user)
