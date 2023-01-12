# Introduction
`mlops-config` defines:
* programmatic model of components involved in typical MLOps workflows,
* project structure conventions,
* configuration schema including conventional default values.

# Getting Started
## Installation
TODO
## Example 1 - Basic
One training and one inference jupyter notebook. Requirements:
* read data from specific directory

Project structure:
```
<PROJECT_ROOT>
    |-- mlops.py
    |__ pipelines
        |-- training.ipynb
        |__ predict.ipynb
```

Required configuration (`mlops.py`):
```python

```

This enables the following components:
* training pipeline that contains a single step defined by the training notebook file,
* (implicitly) model registry,
* batch mode inference pipeline.

## Example 2 - Reusing 
Plus separate data preprocessing notebook, used in both training and inference pipelines

## Example 3 - Real-time model serving
Plus separate script for inference

## Example 4 without notebooks

# Documentation
## Concepts
TODO

## Component Definition Conventions
TODO