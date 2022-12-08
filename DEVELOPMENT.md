TODO: THIS IS OUTDATED - FIX THIS

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