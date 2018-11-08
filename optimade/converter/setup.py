from setuptools import setup

setup(name='MongoConverter',
      version='0.1.0',
      packages=['MongoConverter'],
      entry_points={
          'console_scripts': [
              'MongoConverter = MongoConverter.__main__:main'
          ]
      },
      )
