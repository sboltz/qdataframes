""" Install qdataframes """

try:
    from pathlib import Path
except ImportError:
    raise ImportError("qdataframes requires Python 3+")
from setuptools import setup

package_name = "qdataframes"
encoding = "utf-8"

# Get version information
path = Path(__file__).parent
version = path / package_name / "version.py"
# A bit messy, but this ensures that it doesn't inadvertently grab the wrong thing
txt = version.read_text(encoding=encoding).split("\n")
versions = {}
for v in txt:
    v = v.split("=")  # type: ignore[assignment]
    print(v)
    if len(v) == 2:
        versions[v[0].strip()] = v[1].strip().replace("'", "").replace('"', "")
version = versions["__version__"]

# Get long description
readme = path / "README.md"
readme = readme.read_text(encoding=encoding)

setup(
    name=package_name,
    version=version,
    author="Shawn Boltz",
    author_email="mshawnboltz@gmail.com",
    description="PySide2 models for interacting with pandas DataFrames",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/sboltz/qdataframes",
    project_urls={
        "Bug Tracker": "https://github.com/sboltz/qdataframes/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Development Status :: 3 - Alpha",
        "Topic :: Software Development :: User Interfaces",
    ],
    python_requires=">=3.8",
    install_requires=[
        "versioneer", "pandas>=1.1.3", "PySide2>=5.15.0",
    ],
)
