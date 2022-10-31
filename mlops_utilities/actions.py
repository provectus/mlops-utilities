import json
import logging
from datetime import datetime
from importlib import import_module
from typing import Dict, Optional

import boto3
import sagemaker
from omegaconf import OmegaConf
from sagemaker import (
    Predictor,
    ModelPackage,
    get_execution_role,
    Session
)
from sagemaker.model_monitor import DataCaptureConfig

from mlops_utilities import helpers

logger = logging.getLogger(__name__)


def upsert_pipeline(
        pipeline_module: str,
        pipeline_package: str,
        pipeline_name: str,
        config_type: str,
        role: str,
        pipeline_tags: Optional[Dict[str, str]] = None,
        dryrun: bool = False,
        *args,
):
    """
    Performs Sagemaker pipeline creating or updating.

    Example:
    >>> upsert_pipeline('training_pipeline', 'src', 'a_cool_pipeline_name', 'defaults', 'role-arn', ...)

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

    :param config_type: name of the pipeline yml file with configurations, training_pipeline.<config_type>.yml
    :param role: your IAM role
    :param pipeline_module: a "module path" within the 'pipeline_package' (relative to the 'pipeline_package' root)
    :param pipeline_package: a package where 'pipeline_module' is defined
    :param pipeline_name: the name of the pipeline
    :param pipeline_tags: {"<key>": "<value>", ...} dict to be set as SM pipeline resource tags
    :param dryrun: whether to skip actual pipeline upsert or not
    :param args: extra configuration to pass to pipeline building;
        must follow dot-notation (https://omegaconf.readthedocs.io/en/2.0_branch/usage.html#from-a-dot-list)
    """
    pipeline_module = import_module(f'{pipeline_module}.{pipeline_package}')
    result_conf = helpers.get_pipeline_config(pipeline_module, 'training_pipeline', config_type, role, args)

    if logger.isEnabledFor(logging.INFO):
        logger.info('Result config:\n%s', OmegaConf.to_yaml(result_conf, resolve=True))
    sm_session = Session(default_bucket=OmegaConf.select(result_conf, 'pipeline.default_bucket', default=None))

    pipeline_name = helpers._normalize_pipeline_name(pipeline_name)
    pipe_def = pipeline_module.get_pipeline(sm_session, pipeline_name, result_conf)
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
        pipeline_params={}):
    sm = boto3.client('sagemaker')
    now = datetime.today()
    now_str = helpers.get_datetime_str(now)
    pipe_exec_name = f'{execution_name_prefix}-{now_str}'
    start_pipe_args = {
        'PipelineName': pipeline_name,
        'PipelineExecutionDisplayName': pipe_exec_name,
        'PipelineParameters': [
            {
                'Name': k,
                'Value': str(v)
            }
            for k, v in pipeline_params.items()
        ],
        'ClientRequestToken': helpers.ensure_min_length(pipe_exec_name, 32)
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

    pck = helpers.get_approved_package(sm, model_package_group_name)
    model_description = sm.describe_model_package(ModelPackageName=pck["ModelPackageArn"])

    logger.info("EndpointName= %s", endpoint_name)

    endpoints = sm.list_endpoints(NameContains=endpoint_name)['Endpoints']

    data_capture_config = DataCaptureConfig(
        enable_capture=True, sampling_percentage=100, destination_s3_uri=data_capture_s3_uri
    )

    logger.info("Data capture enabled")

    if len(endpoints) > 0:
        logger.info("Update current endpoint")
        update_endpoint(sm, endpoint_name, data_capture_config)
    else:
        logger.info("Create endpoint")

        model_package_arn = model_description["ModelPackageArn"]
        create_endpoint(model_package_arn, sagemaker_session, instance_count, instance_type, endpoint_name,
                        data_capture_config)


def compare_metrics(sm, des_end_conf, model_statistics_s3_uri, metric):
    model_deployed_description = sm.describe_model(ModelName=des_end_conf["ProductionVariants"][0]["ModelName"])
    model_deployed_description = sm.describe_model_package(
        ModelPackageName=model_deployed_description["Containers"][0]["ModelPackageName"])
    new_model_metrics = helpers.load_json_from_s3(model_statistics_s3_uri)
    old_model_metrics = helpers.load_json_from_s3(
        model_deployed_description["ModelMetrics"]["ModelQuality"]["Statistics"]["S3Uri"])
    metric_path = metric.split('/')

    return helpers.getValueFromDict(new_model_metrics, metric_path[:-1])[metric_path[-1]] > \
           helpers.getValueFromDict(old_model_metrics, metric_path[:-1])[metric_path[-1]]


def update_endpoint(sm, endpoint_name, data_capture_config, model_statistics_s3_uri=None, metric=None):
    des_end_conf = sm.describe_endpoint_config(EndpointConfigName=endpoint_name)
    require_update = True if metric is None else \
        (True if compare_metrics(sm, des_end_conf, model_statistics_s3_uri, metric) else False)

    if require_update:
        predictor = Predictor(endpoint_name=endpoint_name)
        predictor.update_endpoint(initial_instance_count=1,
                                  instance_type='ml.m5.large',
                                  model_name=des_end_conf["ProductionVariants"][0]["ModelName"])
        predictor.update_data_capture_config(data_capture_config)
    else:
        logger.info(
            "Current endpoint is not updated because the new model have worse quality than current deployed model"
        )


def create_endpoint(model_package_arn, sagemaker_session,
                    instance_count, instance_type, endpoint_name,
                    data_capture_config, role=None):
    role = get_execution_role() if role is None else role
    model = ModelPackage(
        role=role, model_package_arn=model_package_arn, sagemaker_session=sagemaker_session
    )

    model.deploy(initial_instance_count=instance_count, instance_type=instance_type, endpoint_name=endpoint_name,
                 data_capture_config=data_capture_config)
