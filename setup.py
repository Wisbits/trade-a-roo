from pathlib import Path
from setuptools import setup, find_packages

DESCRIPTION = (
    "TRADE-O-BOT"
)

APP_ROOT = Path(__file__).parent
README = (APP_ROOT/"README.md").read_text()
AUTHOR = "Rafael Can Savastuerk"
AUTHOR_EMAIL = "r.csavasturk@gmail.com"
INSTALL_REQUIRES = [ 
    "matplotlib==3.4.2",
    "numpy==1.20.3",
    "pandas==1.2.4",
    "requests==2.25.1",
]

setup(
    name="blinkist_task_savasturk",
    description=DESCRIPTION,
    long_description=README,
    long_description_content_type="text/markdown",
    version="0.1",
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    maintainer=AUTHOR,
    maintainer_email=AUTHOR_EMAIL,
    license="MIT",
    packages=find_packages(where="src"),
    package_dir={"":"src"},
    python_requires=">=3.6",
    install_requires=INSTALL_REQUIRES,
)