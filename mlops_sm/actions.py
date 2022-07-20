import json
import boto3
import logging
import sagemaker
from datetime import datetime
from omegaconf import OmegaConf
from importlib import import_module
from sagemaker.model_monitor import DataCaptureConfig
from sagemaker import (
    Predictor,
    ModelPackage,
    get_execution_role,
    Session
)
from typing import Dict, Optional
from .helpers import (
    get_datetime_str,
    ensure_min_length,
    get_approved_package,
    load_json_from_s3,
    get_configs,
    _normalize_pipeline_name
)
from mlops_sm import helpers

logger = logging.getLogger(__name__)


def upsert_pipeline(
        pipeline_module: str,
        pipeline_package: str,
        pipeline_name: str,
        pipeline_tags: Optional[Dict[str, str]] = None,
        dryrun: bool = False,
        *args,
):
    """
    Performs Sagemaker pipeline creating or updating.

    Example:
    >>> upsert_pipeline('training_pipeline', 'src', 'a_cool_pipeline_name', 'role-arn', ...)

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

    :param pipeline_module: a "module path" within the 'pipeline_package' (relative to the 'pipeline_package' root)
    :param pipeline_package: a package where 'pipeline_module' is defined
    :param pipeline_name: the name of the pipeline
    :param pipeline_tags: {"<key>": "<value>", ...} dict to be set as SM pipeline resource tags
    :param dryrun: whether to skip actual pipeline upsert or not
    :param args: extra configuration to pass to pipeline building;
        must follow dot-notation (https://omegaconf.readthedocs.io/en/2.0_branch/usage.html#from-a-dot-list)
    """
    mod_pipe = import_module(f'.{pipeline_module}', pipeline_package)
    result_conf = get_configs(mod_pipe, pipeline_module, args)

    if logger.isEnabledFor(logging.INFO):
        logger.info('Result config:\n%s', OmegaConf.to_yaml(result_conf, resolve=True))
    sm_session = Session(default_bucket=OmegaConf.select(result_conf, 'pipeline.default_bucket', default=None))

    pipeline_name = _normalize_pipeline_name(pipeline_name)
    pipe_def = mod_pipe.get_pipeline(sm_session, pipeline_name, result_conf)
    if logger.isEnabledFor(logging.INFO):
        logger.info("Pipeline definition:\n%s",
                    json.dumps(
                        json.loads(pipe_def.definition()),
                        indent=2
                    ))

    if not dryrun:
        if pipeline_tags is not None:
            pipeline_tags = helpers.convert_param_dict_to_key_value_list(pipeline_tags)
        pipe_def.upsert(result_conf.pipeline.role, tags=pipeline_tags)


def run_pipeline(
        pipeline_name,
        execution_name_prefix,
        dryrun=False,
        **pipe_params):
    sm = boto3.client('sagemaker')
    now = datetime.today()
    now_str = get_datetime_str(now)
    pipe_exec_name = f'{execution_name_prefix}-{now_str}'
    start_pipe_args = {
        'PipelineName': pipeline_name,
        'PipelineExecutionDisplayName': pipe_exec_name,
        'PipelineParameters': [
            {
                'Name': k,
                'Value': str(v)
            }
            for k, v in pipe_params.items()
        ],
        'ClientRequestToken': ensure_min_length(pipe_exec_name, 32)
    }
    if dryrun:
        return start_pipe_args
    else:
        return sm.start_pipeline_execution(**start_pipe_args)


def deploy_model(model_package_group_name, instance_type, instance_count, endpoint_name, data_capture_s3_uri):
    instance_count = int(instance_count)

    boto_sess = boto3.Session()
    sm = boto_sess.client("sagemaker")
    sagemaker_session = sagemaker.Session(boto_session=boto_sess)

    pck = get_approved_package(sm, model_package_group_name)
    model_description = sm.describe_model_package(ModelPackageName=pck["ModelPackageArn"])

    logger.info("EndpointName= %s", endpoint_name)

    endpoints = sm.list_endpoints(NameContains=endpoint_name)['Endpoints']

    data_capture_config = DataCaptureConfig(
        enable_capture=True, sampling_percentage=100, destination_s3_uri=data_capture_s3_uri
    )

    logger.info("Data capture enabled")

    if len(endpoints) > 0:
        logger.info("Update current endpoint")

        model_statistics_s3_uri = model_description["ModelMetrics"]["ModelQuality"]["Statistics"]["S3Uri"]
        update_endpoint(sm, endpoint_name, data_capture_config, model_statistics_s3_uri)

    else:
        logger.info("Create endpoint")

        model_package_arn = model_description["ModelPackageArn"]
        create_endpoint(model_package_arn, sagemaker_session, instance_count, instance_type, endpoint_name,
                        data_capture_config)


def update_endpoint(sm, endpoint_name, data_capture_config, model_statistics_s3_uri):
    des_end_conf = sm.describe_endpoint_config(EndpointConfigName=endpoint_name)
    model_deployed_description = sm.describe_model(ModelName=des_end_conf["ProductionVariants"][0]["ModelName"])
    model_deployed_description = sm.describe_model_package(
        ModelPackageName=model_deployed_description["Containers"][0]["ModelPackageName"])

    new_model_metrics = load_json_from_s3(model_statistics_s3_uri)
    old_model_metrics = load_json_from_s3(
        model_deployed_description["ModelMetrics"]["ModelQuality"]["Statistics"]["S3Uri"])

    if new_model_metrics["binary_classification_metrics"]["accuracy"] > \
            old_model_metrics["binary_classification_metrics"]["accuracy"]:

        predictor = Predictor(endpoint_name=endpoint_name)
        predictor.update_endpoint(model_name=des_end_conf["ProductionVariants"][0]["ModelName"])
        predictor.update_data_capture_config(data_capture_config)
    else:
        logger.info(
            "Current endpoint is not updated because the new model have worse quality than current deployd model"
        )


def create_endpoint(model_package_arn, sagemaker_session,
                    instance_count, instance_type, endpoint_name,
                    data_capture_config):
    role = get_execution_role()
    model = ModelPackage(
        role=role, model_package_arn=model_package_arn, sagemaker_session=sagemaker_session
    )

    model.deploy(initial_instance_count=instance_count, instance_type=instance_type, endpoint_name=endpoint_name,
                 data_capture_config=data_capture_config)
