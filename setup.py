from setuptools import setup

setup(
    name="odo",
    version='1.0',
    py_modules=['odo'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        odo=odo:cli
    ''',
)

