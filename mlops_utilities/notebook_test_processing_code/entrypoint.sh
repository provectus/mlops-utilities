#!/bin/bash

cd /opt/ml/processing/code/
# Exit on any error. SageMaker uses error code to mark failed job.
set -e
if [[ -f 'requirements.txt' ]]; then
    # Some py3 containers has typing, which may breaks pip install
    pip uninstall --yes typing
    pip install -r requirements.txt
fi

pip install --upgrade pip ipython ipykernel
ipython kernel install --name "python3" --user

papermill processing_local_pipeline.ipynb output_processing.ipynb -p role_param arn:aws:iam::311638508164:role/AmazonSageMaker-ExecutionRole -p output_bucket_path kris-mlops-utilities-test
#papermill training_local_pipeline_updated.ipynb output_training.ipynb -p role_param arn:aws:iam::311638508164:role/AmazonSageMaker-ExecutionRole -p output_bucket_path kris-mlops-utilities-test