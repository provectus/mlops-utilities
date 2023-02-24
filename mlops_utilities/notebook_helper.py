"""Jupyter notebook helper"""
import json
import os

from omegaconf import OmegaConf
from sagemaker import Session, TrainingInput
from sagemaker.estimator import Estimator
from sagemaker.processing import FrameworkProcessor, ProcessingInput, ProcessingOutput
from sagemaker.sklearn import SKLearn
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep, TrainingStep

PROCESSING_CONTAINER_DIR = "/opt/ml/processing"


def load_nb_config(nb_config_path: str):
    """

    Args:
        nb_config_path: local path of notebook yml configs

    Returns:
        loaded yml configs
    """
    return OmegaConf.load(nb_config_path)


def create_processor(sm_session: Session, role: str, nb_config_path: str) -> FrameworkProcessor:
    """

    Args:
        sm_session: sagemaker session
        role: role arn
        nb_config_path: local path of notebook yml configs

    Returns:

    """
    nb_config = load_nb_config(nb_config_path)
    return FrameworkProcessor(
        estimator_cls=SKLearn,
        framework_version="0.23-1",
        role=role,
        instance_count=nb_config.training.instance_count,
        instance_type=nb_config.training.instance_type,
        sagemaker_session=sm_session,
    )


def create_processing_step(processing_step_name: str, sm_session: Session, notebook_path: str,
                           role: str, nb_config_path: str) -> ProcessingStep:
    """

    Args:
        processing_step_name: processing step name
        sm_session: sagemaker session
        notebook_path: local path of jupyter notebook
        role: role arn
        nb_config_path: local path of notebook yml configs

    Returns:
        sagemaker processing job
    """
    return ProcessingStep(
        processing_step_name,
        processor=create_processor(sm_session, role, nb_config_path),
        inputs=[
            ProcessingInput(
                input_name="code",
                source=notebook_path,
                destination=os.path.join(PROCESSING_CONTAINER_DIR, "code"),
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="output-data",
                source=os.path.join(PROCESSING_CONTAINER_DIR, "output-data"),
            )
        ],
        code=os.path.join(notebook_path, "entrypoint.sh")
    )


def create_pipeline(pipeline_name: str, sm_session: Session, steps: list, pipeline_params: list) -> Pipeline:
    """

    Args:
        pipeline_name: pipeline name
        sm_session: sagemaker session
        steps: list of composed steps from jupyter notebook
        pipeline_params: pipeline params

    Returns:
        sagemaker pipeline
    """
    return Pipeline(
        name=pipeline_name,
        parameters=pipeline_params,
        steps=steps,
        sagemaker_session=sm_session,
    )


def create_estimator(sm_session: Session, image_uri, role: str, nb_config_path: str, hyperparams_file: str = None):
    """

    Args:
        sm_session: sagemaker session
        image_uri: uri of docker image pushed to sagemaker
        role: role arn
        nb_config_path: local path of notebook yml configs
        hyperparams_file: file with hyperparameters for model

    Returns:
        estimator for training job
    """
    nb_config = load_nb_config(nb_config_path)
    if hyperparams_file:
        with open(hyperparams_file, encoding='utf-8') as json_file:
            hyperparams_dict = json.load(json_file)

    return Estimator(
        image_uri=image_uri,
        instance_type=nb_config.processing.instance_type,
        instance_count=nb_config.processing.instance_count,
        base_job_name="notebook-train",
        sagemaker_session=sm_session,
        role=role,
        hyperparameters=hyperparams_dict
    )


def create_training_step(train_step_name: str, sm_session: Session, image_uri: str, input_data_uri: str,
                         validation_data_uri: str, role: str, nb_config_path: str, hyperparams_file: str = None):
    """

    Args:
        train_step_name: train step name
        sm_session: sagemaker session
        image_uri: image uri
        input_data_uri: input data url
        validation_data_uri: validation data url
        role: role arn
        nb_config_path: local path of notebook yml configs
        hyperparams_file: local path of hyperparameters file

    Returns:

    """
    estimator = create_estimator(sm_session, image_uri, role, nb_config_path, hyperparams_file)
    return TrainingStep(
        name=train_step_name,
        estimator=estimator,
        inputs={
            "train": TrainingInput(
                s3_data=input_data_uri,
                content_type="text/csv",
            ),
            "validation": TrainingInput(
                s3_data=validation_data_uri,
                content_type="text/csv",
            ),
        },
    )


def compose_pipeline(sm_session: Session, role: str, config_yml_path: str, processing: bool = False,
                     training: bool = False, image_uri: str = None, notebook_path: str = None,
                     hyperparams_file=None) -> list:
    """

    Args:
        sm_session: sagemaker session
        role: role arn
        config_yml_path: local path of notebook yml configs
        processing: true IF you want to include processing step
        training: true IF you want to include training step
        image_uri: image uri of pushed image to sagemaker
        notebook_path: local path of notebook yml configs
        hyperparams_file: local path of hyperparameters file

    Returns:
        list of composed steps
    """
    pipeline_steps = []
    if processing:
        processing_step = create_processing_step(
            processing_step_name='processing-nb-upsert',
            sm_session=sm_session,
            notebook_path=notebook_path,
            role=role,
            nb_config_path=config_yml_path
        )
        pipeline_steps.append(processing_step)

    if training:
        training_step = create_training_step(
            train_step_name="training-nb-upsert",
            sm_session=sm_session,
            image_uri=image_uri,
            input_data_uri='s3://kris-mlops-utilities-test/abalone_data/train',
            validation_data_uri='s3://kris-mlops-utilities-test/abalone_data/test',
            role=role,
            nb_config_path=config_yml_path,
            hyperparams_file=hyperparams_file
        )
        pipeline_steps.append(training_step)

    return pipeline_steps
