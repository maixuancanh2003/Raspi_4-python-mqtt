from setuptools import setup, find_packages
import platform

# List of dependencies to be installed via pip
install_requires = [
    'opcua',
    'thread6',
    'asyncio',
    'paho-mqtt',
    'python-snap7',
]

# Linux-specific dependencies to be installed via apt-get
if platform.system() == 'Linux':
    install_requires.extend([
        'RPi.GPIO',
        'rpi-lcd',
        'adafruit-circuitpython-ads1x15',
        # Add other Linux-specific dependencies as needed
    ])
else:
    install_requires.extend([
        'numpy',
        'pandas',
        # Add other platform-specific dependencies as needed
    ])

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='fablab_lib',
    version='0.2.6',
    packages=find_packages(),
    install_requires=install_requires,
    author='FabLab Innovation',
    author_email='thien.dangquang.sistrain@gmail.com',
    description='A package for communicating with PLC via industrial protocols such as OPC UA, Modbus, etc. \
        and logging data to a CSV file.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
    url = 'https://github.com/78-quangSky/MyPackage',
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
