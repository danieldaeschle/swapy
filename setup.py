from setuptools import setup

setup(
    name='swapy',
    version='0.1',
    description='Easy and modular web development',
    author='Daniel Däschle',
    author_email='daniel.daeschle@gmail.com',
    url='https://github.com/danieldaeschle/swapy',
    packages=['swapy'],
    install_requires=['werkzeug', 'jinja2'],
    license='MIT'
)
