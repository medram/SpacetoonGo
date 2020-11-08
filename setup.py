import setuptools

from spacetoongo import __version__

with open('README.md') as f:
    long_description = f.read()

setuptools.setup(
    name='spacetoongo',
    version=__version__,
    description='A simple Spacetoon API for automating stuff instead of Spacetoon Go app using Python.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Mohammed ER-Ramouchy',
    author_email='mohammed@ramouchy.com',
    url='https://github.com/medram/SpacetoonGo',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires='>=3.6',
    packages=setuptools.find_packages(),
    keywords='spacetoon, spacetoon go, spacetoon api',
)
