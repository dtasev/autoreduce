# pylint:skip-file
"""
Wrapper for the functionality for various installation and project setup commands
see:
    `python setup.py help`
for more details
"""
from setuptools import setup

import platform

from build.commands.database import InitialiseTestDatabase
from build.commands.help import Help
from build.commands.installs import InstallExternals
from build.commands.migrate_settings import MigrateTestSettings
from build.commands.start import Start


setup_requires = ['attrs==19.2.0',
                  'dash',
                  'dash_html_components',
                  'dash_core_components',
                  'docker',
                  'Django',
                  'django_extensions',
                  'django_plotly_dash',
                  'django-user-agents',
                  'filelock',
                  'fire',
                  'gitpython',
                  'IPython',
                  'mysqlclient',
                  'mysql-connector',
                  'nexusformat',
                  'numpy',
                  'pandas',
                  'plotly',
                  'pytz',
                  'PyMySQL',
                  'pysftp',
                  'python-icat',
                  'requests',
                  'sentry_sdk',
                  'service_identity',
                  'SQLAlchemy',
                  'stomp.py',
                  'suds-py3',
                  'Twisted',
                  'PyYAML']


if platform.system() == 'Windows':
    setup_requires.append('pypiwin32')
else:
    setup_requires.append('python-daemon')


setup(name='AutoReduction',
      version='20.1',
      description='ISIS AutoReduction service',
      author='ISIS Autoreduction Team',
      url='https://github.com/ISISScientificComputing/autoreduce/',
      install_requires=setup_requires,
      cmdclass={
          'test_settings': MigrateTestSettings,
          'database': InitialiseTestDatabase,
          'externals': InstallExternals,
          'start': Start,
          'help': Help,
      },
     )
