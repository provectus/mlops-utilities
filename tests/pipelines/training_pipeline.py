import os
from pathlib import Path
from omegaconf import OmegaConf
from sagemaker.processing import (
    FrameworkProcessor,
    ProcessingInput,
    ProcessingOutput,
)
from sagemaker.session import Session
from sagemaker.sklearn import SKLearn
from sagemaker.workflow import ParameterString
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import (
    ProcessingStep,
    CacheConfig
)

PROJECT_ROOT = str(Path(__file__).absolute().parents[2])
PREPROCESSING_COMPONENT_SOURCE_DIR = os.path.join(
    PROJECT_ROOT, "tests/components/preprocessing"
)

PROCESSING_CONTAINER_DIR = "/opt/ml/processing"

job_s3_uri_prefix = 's3://kris-predictive-maintenance-test/output/'


# 0.23-1


def create_processor(sagemaker_session, config) -> FrameworkProcessor:
    return FrameworkProcessor(
        estimator_cls=SKLearn,
        framework_version='1.0-1',
        role=config.featurizing.role,
        instance_count=config.featurizing.instance_count,
        instance_type=config.featurizing.instance_type,
        sagemaker_session=sagemaker_session,
        code_location=job_s3_uri_prefix,
    )


# ONLY FOR PROCESSING STEPS
def _step_output_uri(step, output_name):
    return step.properties.ProcessingOutputConfig.Outputs[output_name].S3Output.S3Uri


def get_pipeline(
        sagemaker_session: Session, pipeline_name: str, config: OmegaConf
) -> Pipeline:
    ### CACHING
    cache_config = CacheConfig(**config.pipeline.cache_config)

    #### PARAMETERS
    input_data_s3_uri = "s3://kris-predictive-maintenance-test/abalonelabels/data.csv"
    input_label_s3_uri = "s3://kris-predictive-maintenance-test/abalonedata/data.csv"

    split_processor = create_processor(sagemaker_session, config)

    step_split = ProcessingStep(
        name="AbaloneProcess",
        processor=split_processor,
        inputs=[
            ProcessingInput(
                input_name="data",
                source=input_data_s3_uri,
                destination=os.path.join(PROCESSING_CONTAINER_DIR, "data"),
            ),
            ProcessingInput(
                input_name="label",
                source=input_label_s3_uri,
                destination=os.path.join(PROCESSING_CONTAINER_DIR, "label"),
            ),
            ProcessingInput(
                input_name="split-code",
                source=PREPROCESSING_COMPONENT_SOURCE_DIR,
                destination=os.path.join(PROCESSING_CONTAINER_DIR, "code"),
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="train-dataset-data",
                source=os.path.join(
                    PROCESSING_CONTAINER_DIR, "train-dataset-data"
                ),
            ),
            ProcessingOutput(
                output_name="train-dataset-labels",
                source=os.path.join(
                    PROCESSING_CONTAINER_DIR, "train-dataset-labels"
                ),
            ),
            ProcessingOutput(
                output_name="test-dataset-data",
                source=os.path.join(
                    PROCESSING_CONTAINER_DIR, "test-dataset-data"
                ),
            ),
            ProcessingOutput(
                output_name="test-dataset-labels",
                source=os.path.join(
                    PROCESSING_CONTAINER_DIR, "test-dataset-labels"
                ),
            ),
        ],
        code=os.path.join(PREPROCESSING_COMPONENT_SOURCE_DIR, 'entrypoint.sh'),
        cache_config=cache_config,
        job_arguments=[
            "split",
            "--input-data-path",
            os.path.join(PROCESSING_CONTAINER_DIR, "data"),
            "--input-label-path",
            os.path.join(PROCESSING_CONTAINER_DIR, "label"),
            "--output-train-dataset-data",
            os.path.join(PROCESSING_CONTAINER_DIR, "train-dataset-data"),
            "--output-train-dataset-labels",
            os.path.join(PROCESSING_CONTAINER_DIR, "train-dataset-labels"),
            "--output-test-dataset-data",
            os.path.join(PROCESSING_CONTAINER_DIR, "test-dataset-data"),
            "--output-test-dataset-labels",
            os.path.join(PROCESSING_CONTAINER_DIR, "test-dataset-labels"),
        ],
    )

    pipeline = Pipeline(
        name=pipeline_name,
        steps=[
            step_split,
        ],

        sagemaker_session=sagemaker_session,
    )
    return pipeline
