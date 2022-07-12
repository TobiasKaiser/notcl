import setuptools


setuptools.setup(
    name="notcl",
    version="0.2.1",
    author="Tobias Kaiser",
    author_email="mail@tb-kaiser.de",
    description="Replace Tcl scripting with Python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Tcl",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "License :: OSI Approved :: Apache Software License",
    ],
    python_requires='>=3.6',
    entry_points={
    }
)
