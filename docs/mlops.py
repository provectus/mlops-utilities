from mlops_config.dsl import *
from mlops_config.sagemaker.dsl import *

model_def = file_model("/opt/ml/model")
# first we define components that train a model
project_env = environment_from_sagemaker_kernel_info()
training_step = train_notebook_step(
    code = "pipelines/training.ipynb",
    # kernel
    env = project_env,
    input_datasets = [
        file_dataset("/opt/ml/training-data/"),
    ],
    output_model = model_def,
    # this is optional
    output_metrics = [
        file_metrics("/opt/ml/metrics"),
    ],
)

training_pipeline(
    steps = [training_step]
)

# then we define components that use it for predictions on new data
inference_step = inference_notebook_step(
    code = "pipelines/inference.ipynb",
    env = project_env,
    input_dataset = file_dataset("/opt/ml/input"),
    model = model_def,
    output_dataset = file_dataset("/opt/ml/output"),
)

inference_pipeline(
    steps = [inference_step]
)