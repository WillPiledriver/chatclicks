from setuptools import setup, find_packages

setup(
    name='chatclicks',
    version='0.4.2',  # Update the version for each release
    description='A package for handling chat clicks through websockets.',
    author='WillPiledriver',
    author_email='smifthsmurfth@gmail.com',
    url='https://github.com/WillPiledriver/chatclicks',
    packages=find_packages(),
    install_requires=[
        'python-socketio',
        'scikit-learn',
        'numpy',
        'aiohttp',
        'asyncio'
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)