# MLOps Utilities

## Intro
MLOps Utilities provides:
- Implementation of high level operations most commonly occuring in workflows for production-ready ML models:
  - Implement the simplest dataset versioning
  - Develop a model training pipeline
  - Schedule its execution on timely or event-triggered execution, e.g., new dataset version
  - Zero-config experiment tracking
  - Zero-config model versioning and model registry
  - Deploy model
    * Create endpoint
    * Update endpoint
  - Setup monitoring
    * data quality monitoring for checking health of input data sources
    * model quality monitoring for checking health of model output
- In AWS cloud.

## Concepts
MLOps Utilities work on the specific project structure conventions described below.
Use cases are sorted according to the amount of efforts required to implement full MLOps workflow using this library.

## Use cases
### The simplest case
You made a single IPython/Jupyter notebook that:
* takes as input a training dataset location
* preprocess data using Pandas
* train model using scikit-learn
* evaluate model using scikit-learn and print reports using matplotlib.

### ~~Just slightly changed~~
~~You want to scale img-2-img stable diffusion that you finetuned for the most popular and money generation use cases~~:
* ~~transforming your day-to-day casual boring iphone videos to epic anime battles~~.

## User guide
#### Installation
`pip3 install mlops-utilities`
#### Project structure conventions
TODO
#### Actions
TODO
```
from mlops_utilities.actions import run_pipeline
    
run_pipeline(
  pipeline_name='test_pipeline',
  execution_name_prefix='test_pipeline',
  dryrun=True,
  pipeline_params={}
)
```
