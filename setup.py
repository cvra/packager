from setuptools import setup

setup(
    name='cvra-packager',
    version='1.0.0',
    description='CVRA packaging system',
    author='Club Vaudois de Robotique Autonome',
    author_email='info@cvra.ch',
    url='https://github.com/cvra/packager',
    license='BSD',
    packages=['cvra_packager'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Embedded Systems',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        ],
    install_requires=[
        'pyyaml',
        'jinja2',
        ],
    package_data = {
        '': ['*.jinja'],
        },
    entry_points={
        'console_scripts': [
            'packager=cvra_packager.packager:main',
            ],
        },
    )

