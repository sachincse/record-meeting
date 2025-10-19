from setuptools import setup, find_packages
import pathlib
import re

HERE = pathlib.Path(__file__).parent.resolve()

# Read version from recordmymeeting/__init__.py without importing
def read_version():
    init_py = (HERE / "recordmymeeting" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r"^__version__\s*=\s*['\"]([^'\"]+)['\"]", init_py, re.M)
    if not match:
        raise RuntimeError("Unable to find __version__ in recordmymeeting/__init__.py")
    return match.group(1)

long_description = (HERE / "README.md").read_text(encoding="utf-8")

setup(
    name="recordmymeeting",
    version=read_version(),
    author="Sachin Singh",
    author_email="sachincs95@gmail.com",
    description="Effortlessly capture audio and screen with intelligent device detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sachincse/recordmymeeting",
    project_urls={
        "Bug Tracker": "https://github.com/sachincse/recordmymeeting/issues",
        "Documentation": "https://github.com/sachincse/recordmymeeting#readme",
        "Source Code": "https://github.com/sachincse/recordmymeeting",
    },
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pyaudio>=0.2.11",
        "opencv-python>=4.8.0",
        "numpy>=1.19.0",
        "mss>=6.1.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Operating System :: OS Independent",
        "Topic :: Multimedia :: Sound/Audio :: Capture/Recording",
        "Topic :: Multimedia :: Video :: Capture",
    ],
    entry_points={
        "console_scripts": [
            "recordmymeeting=recordmymeeting.cli:main",
            "recordmymeeting-gui=recordmymeeting.gui_app:launch_gui",
        ],
    },
)
