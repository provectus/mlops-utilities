# MLOps Utilities

This library provides implementation for a few high level operations most commonly occuring in any MLOps workflows built in AWS:
- Upsert pipeline
- Run pipeline
- Deploy model
    - Create endpoint
    - Update endpoint

### User guide
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
