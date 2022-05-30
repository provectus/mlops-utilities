import os
import setuptools


setuptools.setup(
    name="mlops-utilities",
    version=os.environ['PACKAGE_VERSION'].strip(),
    author="Provectus",
    author_email="ml@provectus.com",
    description="A set of utils for MLOps tasks.",
    install_requires=['sagemaker==2.92.1', 'omegaconf==2.1.2'],
    packages=['mlops_utilities'],
    url='https://gitlab.provectus.com/mldemo/mlops-platform/mlops-utilities',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
    python_requires='>=3.8',
)
