# MLOps Utilities

## Intro
MLOps Utilities provides:
- Implementation of high level operations most commonly occuring in workflows for production-ready ML models:
  - Dataset versioning
  - Building of training pipeline from initial code sources: Jupyter notebooks, python modules, etc.
  - Training pipeline deployment
  - Scheduling its execution on timely or event-triggered execution, e.g., new dataset version
  - Zero-config lineage tracking
  - Zero-config model versioning and model registry
  - Model packaging and deployment
  - Model endpoint management
  - Data quality monitoring setup
  - Model quality monitoring setup
- In AWS cloud.

## Installation
`pip install mlops-utilities`

## User Guide
### Concepts
This library simplifies MLOps workflow implementation by greatly reducing amount of boilerplate code and configuration required. It does so by relying on specific conventions for project structure  described below.

Use cases are sorted by increasing complexity.

### \[NOT IMPLEMENTED\] The simplest case
You made a single Jupyter notebook that:
* takes as input a training dataset location
* preprocess data using Pandas
* train model using scikit-learn
* evaluate model using scikit-learn
* uses one of the predefined kernels of Sagemaker Studio as an execution environment.
* You have not changed this environment with `pip install`s. If you did then check the next use case.

#### You prepared / Project Structure:
```
<PROJECT_ROOT>
  |-- my_project07.ipynb
```

#### Library usage:
To build and deploy pipeline (in SageMaker) use the following CLI command:
```
mlops upsert-pipeline TODO header of help description for this command
```
or from code:
```python
from mlops_utilities.actions import upsert_pipeline
...
TODO
upsert_pipeline(TODO args example)
```

To execute the previously upserted pipeline:
```
mlops run-pipeline TODO
```

Training pipeline execution produces new model version in model registry. To deploy it onto real-time endpoint use the following CLI command:
```
mlops deploy-model TODO
```

### \[NOT IMPLEMENTED\] The "simple" layout
TODO - The same as default layout but without writing pipeline definition using SageMaker SDK.

### The "default" layout
If you separated code of different pipeline steps and defined training pipeline using SageMaker SDK.

#### You prepared / Project Structure:
```
<PROJECT_ROOT>
  |-- components
          |-- preprocessing
                  |-- preprocess.py
                  |__ requirements.txt
          |-- training
                  |__ train.py
          |__ <folders for other steps>
  |-- pipelines
          |-- training_pipeline.py
          |-- training_pipeline.defaults.conf
          |-- inference_pipeline.py
          |__ inference_pipeline.defaults.conf
```
#### TODO describe pipeline definition structure

#### TODO describe component implementations and environments

#### Library usage:
To build and deploy pipeline (in SageMaker) use the following CLI command:
```
mlops upsert-pipeline TODO header of help description for this command
```
or from code:
```python
from mlops_utilities.actions import upsert_pipeline
...
TODO
upsert_pipeline(TODO args example)
```

To execute the previously upserted pipeline:
```
mlops run-pipeline TODO
```

Training pipeline execution produces new model version in model registry. To deploy it onto real-time endpoint use the following CLI command:
```
mlops deploy-model TODO
```