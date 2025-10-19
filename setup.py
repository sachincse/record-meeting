from setuptools import setup, find_packages

long_description = "RecordFlow: Effortlessly capture audio and screen with intelligent device detection"

setup(
    name="recordflow",
    version="0.1.2",
    author="Your Name",
    author_email="your_email@example.com",
    description="Effortlessly capture audio and screen with intelligent device detection",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "pyaudio>=0.2.11",
        "opencv-python>=4.8.0",
        "numpy>=1.19.0",
        "mss>=6.1.0",
    ],
    entry_points={
        "console_scripts": [
            "recordflow=recordflow.cli:main",
            "recordflow-gui=recordflow.gui_app:launch_gui",
        ],
    },
)
