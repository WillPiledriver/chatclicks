from setuptools import setup, find_packages

setup(
    name='chatclicks',
    version='0.1.0',  # Update the version for each release
    description='A package for handling chat clicks through websockets.',
    author='WillPiledriver',
    author_email='smifthsmurfth@gmail.com',
    url='https://github.com/WillPiledriver/chatclicks',
    packages=find_packages(),
    install_requires=[
        'python-socketio',
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)