"""Sagemaker actions"""
import json
import logging
from datetime import datetime
from importlib import import_module
from typing import Any, Dict, NoReturn, Optional

import boto3
from omegaconf import OmegaConf
from sagemaker import ModelPackage, Predictor, Session
from sagemaker.model_monitor import DataCaptureConfig
from sagemaker.workflow.pipeline_context import PipelineSession

from mlops_utilities import helpers

logger = logging.getLogger(__name__)


def upsert_pipeline(
    pipeline_module: str,
    pipeline_package: str,
    pipeline_name: str,
    config_type: str,
    role: str,
    *args,
    pipeline_tags: Optional[Dict[str, str]] = None,
    dryrun: bool = False,
) -> NoReturn:
    """
    Performs Sagemaker pipeline creating or updating.

    Example:
    >>> upsert_pipeline('training_pipeline', 'src', 'a_cool_pipeline_name', 'training.defaults', 'role-arn', ...)

    First two arguments is set so to follow (folder) package structure described below
    when the function is invoked from the root dir:
        root
        |
        |-- src
        |   |-- training_pipeline.py
        |   |-- ...
        |   `-- ...
        |
        ...

    :param config_type: name of the pipeline yml file with configurations, <training_pipeline>.<config_type>
    :param role: your IAM role
    :param pipeline_module: a "module path" within the 'pipeline_package' (relative to the 'pipeline_package' root)
    :param pipeline_package: a package where 'pipeline_module' is defined
    :param pipeline_name: the name of the pipeline
    :param pipeline_tags: {"<key>": "<value>", ...} dict to be set as SM pipeline resource tags
    :param dryrun: whether to skip actual pipeline upsert or not
    :param args: extra configuration to pass to pipeline building;
        must follow dot-notation (https://omegaconf.readthedocs.io/en/2.0_branch/usage.html#from-a-dot-list)
    """
    pipeline_module = import_module(f"{pipeline_module}.{pipeline_package}")
    result_conf = helpers.get_pipeline_config(
        pipeline_module, config_type, role, list(args)
    )

    if logger.isEnabledFor(logging.INFO):
        logger.info("Result config:\n%s", OmegaConf.to_yaml(result_conf, resolve=True))
    sm_session = PipelineSession(
        default_bucket=OmegaConf.select(
            result_conf, "pipeline.default_bucket", default=None
        )
    )

    pipeline_name = helpers.normalize_pipeline_name(pipeline_name)
    pipeline_object = pipeline_module.get_pipeline(
        sm_session, pipeline_name, result_conf
    )
    if logger.isEnabledFor(logging.INFO):
        logger.info(
            "Pipeline definition:\n%s",
            json.dumps(json.loads(pipeline_object.definition()), indent=2),
        )

    if not dryrun:
        if pipeline_tags is not None:
            pipeline_tags = helpers.convert_param_dict_to_key_value_list(pipeline_tags)
        pipeline_object.upsert(result_conf.pipeline.role, tags=pipeline_tags)


def run_pipeline(
    pipeline_name: str,
    execution_name_prefix: str,
    pipeline_params: Dict[str, Any],
    dryrun=False,
) -> str:
    """
    Performs Sagemaker pipeline running.
    !!! This pipeline should be created and should be uploaded to Sagemaaker.

    Example:
    >>> run_pipeline('a_cool_pipeline_name', 'training_exec')

    :param pipeline_name: uploaded Sagemaker pipeline name
    :param execution_name_prefix: prefix for pipeline running job
    :param dryrun: should be run in test mode without real execution. If true then the method returns only arguments
    :param pipeline_params: additional parameters for pipeline
    """
    sagemaker_client = boto3.client(
        "sagemaker"
    )  # Can not be cut off because it could not be presented as string
    now = datetime.today()
    now_str = helpers.get_datetime_str(now)
    pipe_exec_name = f"{execution_name_prefix}-{now_str}"
    start_pipe_args = {
        "PipelineName": pipeline_name,
        "PipelineExecutionDisplayName": pipe_exec_name,
        "PipelineParameters": helpers.convert_param_dict_to_key_value_list(
            pipeline_params
        ),
    }
    if dryrun:
        return str(start_pipe_args)
    return sagemaker_client.start_pipeline_execution(**start_pipe_args)


def deploy_model(
    sagemaker_session: Session,
    model_package_group_name: str,
    instance_type: str,
    instance_count: int,
    endpoint_name: str,
    data_capture_s3_uri: str,
    role: str,
) -> NoReturn:
    """
    Method deploys model to Sagemaker
    :param sagemaker_session: Sagemaker Session
    :param model_package_group_name: destination model package of deploying
    :param instance_type: instance types on which the model is deployed
    :param instance_count: amount of instances on which the model is deployed
    :param endpoint_name:
    :param data_capture_s3_uri: s3 bucket which accumulates data capture
    :param role: execution IAM role
    """
    instance_count = int(instance_count)

    sagemaker_client = sagemaker_session.sagemaker_client

    pck = helpers.get_approved_package(sagemaker_client, model_package_group_name)
    model_description = sagemaker_client.describe_model_package(
        ModelPackageName=pck["ModelPackageArn"]
    )
    if logger.isEnabledFor(logging.INFO):
        logger.info("EndpointName= %s", endpoint_name)

    endpoints = sagemaker_client.list_endpoints(NameContains=endpoint_name)["Endpoints"]

    data_capture_config = DataCaptureConfig(
        enable_capture=True,
        sampling_percentage=100,
        destination_s3_uri=data_capture_s3_uri,
    )
    if logger.isEnabledFor(logging.INFO):
        logger.info("Data capture enabled")

    if len(endpoints) > 0:
        if logger.isEnabledFor(logging.INFO):
            logger.info("Update current endpoint")
        update_endpoint(
            sagemaker_client,
            instance_type,
            instance_count,
            endpoint_name,
            data_capture_config,
        )
    else:
        if logger.isEnabledFor(logging.INFO):
            logger.info("Create endpoint")

        model_package_arn = model_description["ModelPackageArn"]
        create_endpoint(
            model_package_arn,
            sagemaker_session,
            instance_count,
            instance_type,
            endpoint_name,
            data_capture_config,
            role,
        )


def compare_metrics(
    sagemaker_client,
    endpoint_config_description: Dict[str, Any],
    model_statistics_s3_uri: str,
    metric: str,
    dryrun: bool = False,
) -> bool:
    """
    This method compares metrics of old and new model versions
    :param sagemaker_client: boto3_session_client(sagemaker)
    :param endpoint_config_description: endpoint configuration
    :param model_statistics_s3_uri: s3 bucket which contains evaluation metrics
    :param metric: path to metric in json file, example: 'regression_metrics/mse/value'
    :param dryrun: is True in case of test
    :return: result of metric comparison
    """
    model_deployed_description = sagemaker_client.describe_model(
        ModelName=endpoint_config_description["ProductionVariants"][0]["ModelName"]
    )
    model_deployed_description = sagemaker_client.describe_model_package(
        ModelPackageName=model_deployed_description["Containers"][0]["ModelPackageName"]
    )
    test_json_metrics = {"regression_metrics": {"mse": {"value": 4}}}
    new_model_metrics = (
        test_json_metrics
        if dryrun
        else helpers.load_json_from_s3(model_statistics_s3_uri)
    )
    old_model_metrics = (
        test_json_metrics
        if dryrun
        else helpers.load_json_from_s3(
            model_deployed_description["ModelMetrics"]["ModelQuality"]["Statistics"][
                "S3Uri"
            ]
        )
    )
    metric_path = metric.split("/")

    new_metric = helpers.get_value_from_dict(new_model_metrics, metric_path[:-1])[
        metric_path[-1]
    ]
    old_metric = helpers.get_value_from_dict(old_model_metrics, metric_path[:-1])[
        metric_path[-1]
    ]
    return new_metric >= old_metric


def update_endpoint(
    sagemaker_client,
    instance_type: str,
    instance_count: int,
    endpoint_name: str,
    data_capture_config: DataCaptureConfig,
    model_statistics_s3_uri: Optional[str] = None,
    metric: Optional[str] = None,
    dryrun: bool = False,
) -> NoReturn:
    """
    Updating Sagemaker endpoint
    :param sagemaker_client: boto3_session_client(sagemaker)
    :param instance_type
    :param instance_count
    :param endpoint_name:
    :param data_capture_config: config for inference data capture
    :param model_statistics_s3_uri: s3 bucket which contains evaluation metrics
    :param metric: path to metric value in `model_statistics_s3_uri`
    :param dryrun: is 'True' in a case of testing
    :return:
    """
    endpoint_config_description = sagemaker_client.describe_endpoint_config(
        EndpointConfigName=endpoint_name
    )
    model_name = (
        endpoint_config_description["ProductionVariants"][0]["ModelName"]
        if not dryrun
        else "model"
    )
    require_update = metric is None or (
        metric is not None
        and compare_metrics(
            sagemaker_client,
            endpoint_config_description,
            model_statistics_s3_uri,
            metric,
        )
    )

    if require_update:
        predictor = Predictor(endpoint_name=endpoint_name)
        predictor.update_endpoint(
            initial_instance_count=instance_count,
            instance_type=instance_type,
            model_name=model_name,
        )
        predictor.update_data_capture_config(data_capture_config)
    else:
        if logger.isEnabledFor(logging.INFO):
            logger.info(
                "Current endpoint is not updated because the new model have worse quality than current deployed model"
            )


def create_endpoint(
    model_package_arn: str,
    sagemaker_session: Session,
    instance_count: int,
    instance_type: str,
    endpoint_name: str,
    data_capture_config: DataCaptureConfig,
    role: str,
) -> None:
    """
    It executes endpoint creation into Sagemaker
    :param model_package_arn: model package descriptor
    :param sagemaker_session: Sagemaker Session
    :param instance_count: amount of instances on which the model is deployed
    :param instance_type: instance types on which the model is deployed
    :param endpoint_name: endpoint name as string
    :param data_capture_config: config for inference data capture
    :param role: execution IAM role
    :return: None
    """
    model = ModelPackage(
        role=role,
        model_package_arn=model_package_arn,
        sagemaker_session=sagemaker_session,
    )

    model.deploy(
        initial_instance_count=instance_count,
        instance_type=instance_type,
        endpoint_name=endpoint_name,
        data_capture_config=data_capture_config,
    )
