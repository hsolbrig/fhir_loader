from distutils.core import setup

setup(
    name='fhir_loader',
    version="0.0.1",
    packages=['fhir_loader'],
    url='https://github.com/hsolbrig/fhir_loader',
    license='Apache 2.0',
    author='Harold Solbrig',
    author_email='solbrig@jhu.edu',
    description='FHIR loading tool',
    long_description='Utility for uploading files, directories and other content into FHIR',
    install_requires=["requests"],
    scripts=['scripts/fhir_loader'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Topic :: Database',
        'Programming Language :: Python :: 3'
    ]
)
