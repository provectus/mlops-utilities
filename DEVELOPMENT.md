- [Development](#development)
  - [Required tools](#required-tools)
  - [Create project environment](#create-project-environment)
  - [Configure access](#configure-access)
  - [Unit tests](#unit-tests)
  - [Preparing release version](#preparing-release-version)
  - [Build \& Publish](#build--publish)
  - [How to import it in edit mode into other projects for development](#how-to-import-it-in-edit-mode-into-other-projects-for-development)
- [CI/CD](#cicd)
    - [Any commits](#any-commits)
    - [Commits to `main`](#commits-to-main)
    - [Tags](#tags)

# Development
## Required tools
`Poetry` is used as a build system, dependency manager and publisher for this project.
See poetry installation instructions [here](https://python-poetry.org/docs/#installation).

## Create project environment
(in the root project directory) Run:
```
poetry install
```
After that poetry will create a separate virtual environment and install all required packages plus the package itself into this virtual env. This virtual env can be used to setup your IDE - both VSCode and PyCharm can discover poetry virtual environments.

## Configure access
Provide access token for publishing destination (PyPI) - in unlikely event if you have to publish there manually:
```
poetry config pypi-token.pypi "<YOUR_TOKEN_FROM_PYPI_ACCOUNT>"
```
You can generate this token in your [PyPI account settings](https://pypi.org).

## Unit tests
Run:
```
make test
```

## Preparing release version
If tests are successfull you can update package version (to be later published) by running:
```
poetry version patch
```
Once you bumped the version you are expected to publish this version, but this part is automated in CI. The next section below explains how to do it manually.

## Build & Publish
To build wheel (and sdist) run:
```
poetry build
```

And then to publish it into PyPi:
```
poetry publish
```
Congrats!

## How to import it in edit mode into other projects for development
See `path` dependency specification described [here](https://python-poetry.org/docs/dependency-specification/#path-dependencies).

# CI/CD
### Any pull request
Github Actions runs unit testing and lint testing

### Manually Build and Publish packages via Github Actions workflow
Select Publish workflow -> Run workflow -> select version format for auto versioning (major, minor, path) :

This workflow:
* runs units testing
* invokes poetry to increase version
* invokes poetry to build package
* creates tag and releases with a new version
* invokes poetry to publish package
* commits these changes
* and pushes all of these to the git repo.
