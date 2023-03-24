import setuptools


setuptools.setup(
    name="notcl",
    version="0.3.2",
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
    python_requires='>=3.8',
    entry_points={
    }
)
