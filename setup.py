# SPDX-FileCopyrightText: 2024 Tobias Kaiser <mail@tb-kaiser.de>
# SPDX-License-Identifier: Apache-2.0

import setuptools

exec(open('notcl/version.py').read()) # --> __version__

setuptools.setup(
    name="notcl",
    version=__version__,
    author="Tobias Kaiser",
    author_email="mail@tb-kaiser.de",
    description="Replace Tcl scripting with Python",
    packages=setuptools.find_packages(),
    package_data={'': ['*.tcl']},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Tcl",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "License :: OSI Approved :: Apache Software License",
    ],
    python_requires='>=3.9',
    entry_points={
    }
)
