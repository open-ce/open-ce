#!/usr/bin/env python

"""
# *****************************************************************
# (C) Copyright IBM Corp. 2021. All Rights Reserved.
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
# *****************************************************************
"""
from setuptools import find_packages, setup
import open_ce

def get_readme():
    with open("README.md") as f:
        return f.read()


REQUIRED_PACKAGES = [
    "pyyaml",
    "requests",
    "jinja2",
]

setup(
    name="open-ce",
    version=open_ce.__version__,
    description="Open-CE tools for building feedstocks",
    long_description=get_readme(),
    url="https://github.com/open-ce/open-ce",
    author="Open-CE Dev Team",
    author_email="",
    packages = find_packages(),
    scripts = ["open_ce/open-ce"],
    include_package_data=True,
    package_data={
        "open_ce": [
            "open_ce/images",
            "doc",
        ],
    },

    python_requires=">= 3.6",
    install_requires=REQUIRED_PACKAGES,
    tests_require=["pytest"],
    # PyPI package information.
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries",
    ],
    license="Apache 2.0",
    keywords="Machine learning, build tools",
)
