# -*- coding: utf-8 -*-
from setuptools import setup

packages = \
['qcrew',
 'qcrew.analyze',
 'qcrew.control',
 'qcrew.control.instruments',
 'qcrew.control.instruments.meta',
 'qcrew.control.instruments.qm',
 'qcrew.control.instruments.signal_hound',
 'qcrew.control.instruments.vaunix',
 'qcrew.control.modes',
 'qcrew.control.pulses',
 'qcrew.control.stage',
 'qcrew.helpers',
 'qcrew.measure']

package_data = \
{'': ['*']}

install_requires = \
['PyYAML>=5.4.1,<6.0.0',
 'Pyro5>=5.12,<6.0',
 'h5py>=3.3.0,<4.0.0',
 'ipykernel>=6.0.2,<7.0.0',
 'ipython>=7.25.0,<8.0.0',
 'loguru>=0.5.3,<0.6.0',
 'matplotlib>=3.4.2,<4.0.0',
 'numpy>=1.21.0,<2.0.0',
 'qm @ https://qm-pypi-repository.s3.amazonaws.com/qm-0.90.1736.tar.gz']

extras_require = \
{':python_version >= "3.9" and python_version < "3.10"': ['scipy>=1.7.0,<2.0.0']}

setup_kwargs = {
    'name': 'qcrew',
    'version': '0.1.0',
    'description': "The codebase for running circuit QED experiments in QCREW's lab",
    'long_description': None,
    'author': 'QCREW',
    'author_email': 'hello.qcrew@gmail.com',
    'maintainer': None,
    'maintainer_email': None,
    'url': None,
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'extras_require': extras_require,
    'python_requires': '>=3.9,<4.0',
}


setup(**setup_kwargs)
