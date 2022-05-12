# MLOps Utilities SDK

### Description
SDK contains next methods used to operate with AWS SageMaker entities:
- Upsert pipeline
- Run pipeline
- Deploy model
    - Create endpoint
    - Update endpoint

### Build and push
AWS CodeArtifact is used as a package repository. Package is built and pushed to AWS CodeArtifact by GitLab CI/CD.

Once there is a version to deploy, you need to manually trigger `build-package` CI/CD job that executes next actions:
- update the version
- build the package
- upload the package to AWS CodeArtifact (via twine)

Using following commands you can build and test locally (from root dir):
```
python3 setup.py bdist_wheel
pip3 install dist/mlops_utilities-{version}-py3-none-any.whl
```

### Install/Usage
To install the package from AWS CodeArtifact run:
```
make setup_pip CA_DOMAIN_NAME={#domain} CA_DOMAIN_OWNER={#account_id} AWS_DEFAULT_REGION={#region}
pip3 install mlops-utilities
```

Usage example:
```
from mlops_utilities.actions import run_pipeline
    
run_pipeline(
  pipeline_name='test_pipeline',
  execution_name_prefix='test_pipeline',
  dryrun=True
)
```
