from distutils.core import setup

setup(
  name = 'mlops_sm',  
  version=open("version", "r").read(),
  packages = ['mlops_sm'],   
  license='MIT',       
  description = 'Utility package for MlOps project',   
  author = 'Provectus Team',                   
  author_email = 'abelov@provectus.com',     
  download_url = 'https://gitlab.provectus.com/mldemo/mlops-platform/mlops-utilities/-/archive/0.0.19/mlops-utilities-0.0.19.tar.gz',    # I explain this later on
  keywords = ['MLOps', 'Utility package'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
          'boto3',
          'sagemaker',
          'datetime',
          'omegaconf',
          'importlib',
          'pathlib',
          'botocore'
      ],
  classifiers=[
    'Development Status :: 4 - Beta',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      # Define that your audience are developers
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
  ],
)
