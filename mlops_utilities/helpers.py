"""MLOps Utilities helpers"""
import json
import logging
import operator
from datetime import datetime
from functools import reduce
from pathlib import Path
from typing import Any, Dict, List, Mapping

import boto3  # type: ignore
from botocore.client import BaseClient  # type: ignore
from omegaconf import OmegaConf, dictconfig

# Sagemaker dependent methods
from sagemaker import Session
from sagemaker.workflow.pipeline import Pipeline

from mlops_utilities.notebook_helper.processing_helper import ProcessingHelper
from mlops_utilities.notebook_helper.training_helper import TrainingHelper

logger = logging.getLogger(__name__)


def get_pipeline_config(
        pipeline_module, config_type: str, pipeline_role: str, args: List
) -> dictconfig.DictConfig:
    """
    Read pipeline config
    :param pipeline_module: python module which includes pipeline
    :param config_type: config filename
    :param pipeline_role: IAM role
    :param args: runtime pipeline arguments
    :return: OmegaConf Dict Config
    """
    default_conf_path = f"{Path(pipeline_module.__file__).parent}/{config_type}.yml"
    default_conf = OmegaConf.load(default_conf_path)
    arg_conf = OmegaConf.create({"pipeline": {"role": pipeline_role}})
    override_arg_conf = OmegaConf.from_dotlist(args)
    return OmegaConf.merge(default_conf, arg_conf, override_arg_conf)


def get_output_destination(
        sagemaker_client: BaseClient, processing_job_arn: str, output_name: str
) -> str:
    """
    Get the S3 URI of the output destination for a processing job.

    :param sagemaker_client: An instance of `boto3.client("sagemaker")`.
    :param processing_job_arn: The ARN of the processing job.
    :param output_name: The name of the output.
    :return: The S3 URI of the output destination.
    """
    pj_output_dict = _list_to_dict(
        sagemaker_client.describe_processing_job(
            ProcessingJobName=get_job_name(processing_job_arn)
        )["ProcessingOutputConfig"]["Outputs"],
        "OutputName",
    )
    return pj_output_dict[output_name]["S3Output"]["S3Uri"]


def get_model_location(sagemaker_client: BaseClient, model_name: str) -> str:
    """
    Get the S3 URI of a model.

    :param sagemaker_client: An instance of `boto3.client("sagemaker")`.
    :param model_name: The name of the model.
    :return: The S3 URI of the model.
    """
    model_desc = sagemaker_client.describe_model(ModelName=model_name)
    return model_desc["PrimaryContainer"]["ModelDataUrl"]


def get_approved_package(
        sagemaker_client: BaseClient, model_package_group_name: str
) -> Dict[str, Any]:
    """
    Get the most recent approved model package in a model package group.

    :param sagemaker_client: An instance of `boto3.client("sagemaker")`.
    :param model_package_group_name: The name of the model package group.
    :return: A dictionary containing information about the approved model package.
    :raises ValueError: If no approved model packages are found in the specified group.
    """
    response = sagemaker_client.list_model_packages(
        ModelApprovalStatus="Approved",
        ModelPackageGroupName=model_package_group_name,
        SortBy="CreationTime",
        SortOrder="Descending",
        MaxResults=1,
    )

    model_packages = response["ModelPackageSummaryList"]
    if len(model_packages) == 0:
        raise ValueError(
            f"No approved ModelPackage found for ModelPackageGroup: {model_package_group_name}"
        )

    return model_packages[0]


def load_json_from_s3(s3_uri: str) -> Dict:
    """
    Load a JSON file from an S3 bucket and return the contents as a dictionary.

    :param s3_uri: The S3 URI of the JSON file (e.g. "s3://my-bucket/path/to/file.json").
    :return: The contents of the JSON file as a dictionary.
    """
    s3_client = boto3.client("s3")
    bucket, key = s3_uri.replace("s3://", "").split("/", 1)
    s3_response_object = s3_client.get_object(Bucket=bucket, Key=key)

    return json.loads(s3_response_object["Body"].read().decode("utf-8"))


def create_model_from_model_package(
        sagemaker_client: BaseClient,
        model_name: str,
        model_package_arn: str,
        execution_role: str,
        tags: List[Dict[str, str]],
) -> str:
    """
    Create a model from a model package and return the model ARN.

    :param sagemaker_client: An instance of `boto3.client("sagemaker")`.
    :param model_name: The name of the model.
    :param model_package_arn: The ARN of the model package.
    :param execution_role: The ARN of the IAM role that will be used for the model.
    :param tags: A list of tags to apply to the model. Each tag is a dictionary with two keys: "Key" and "Value".
    :return: The ARN of the created model.
    """
    response = sagemaker_client.create_model(
        ModelName=model_name,
        Containers=[{"ModelPackageName": model_package_arn}],
        ExecutionRoleArn=execution_role,
        Tags=tags,
    )
    return response["ModelArn"]


# Common methods


def get_datetime_str(date_time: datetime) -> str:
    """
    Convert datetime to string
    :param date_time:
    :return: string
    """
    return date_time.strftime("%Y-%m-%d-%H-%M-%S")


def convert_param_dict_to_key_value_list(
        arg_dict: Dict[str, str]
) -> List[Dict[str, str]]:
    """
    Convert python dict to Sagemaker SDK resource tags structure
    where dict key corresponds to "Name", dict value corresponds to "Value".
    :param arg_dict: key-value need to convert to AWS resource tags structure
    :return: list of tags in the following format: [ { "Key": "...", "Value": "..." }, ... ]
    """
    return [{"Key": k, "Value": v} for k, v in arg_dict.items()]


def convert_param_dict_to_name_value_list(
        arg_dict: Dict[str, str]
) -> List[Dict[str, str]]:
    """
    Convert python dict to Sagemaker SDK resource tags structure
    where dict key corresponds to "Name", dict value corresponds to "Value".
    :param arg_dict: key-value need to convert to AWS resource tags structure
    :return: list of tags in the following format: [ { "Name": "...", "Value": "..." }, ... ]
    """
    return [{"Name": str(k), "Value": str(v)} for k, v in arg_dict.items()]


def get_value_from_dict(data_dict: Dict[str, Any], path: List[str]) -> Mapping:
    """
    Get necessary metric from evaluation.json
    :param data_dict: dictionary that contains metrics {"regression_metrics": {"mse":..}}
    :param path: path to metric ['regression_metrics','mse',…]
    :return: dictionary that contains target metric:
    for example {mse: 2.1} --from--> { "Key 01": { "Key 02:…{mse: 2.1}"}
    """
    return reduce(operator.getitem, path, data_dict)


def normalize_key(key: str) -> str:
    """
    Remove _ from keys and lower case it
    :param key:
    :return key:
    """
    return key.replace("_", "").lower()


def get_model_name(model_arn: str) -> str:
    """
    Get model name from ARN
    :param model_arn:
    :return model name:
    """
    return model_arn[model_arn.rindex("/") + 1:]


def get_job_name(job_arn: str) -> str:
    """
    Get job name from ARN
    :param job_arn:
    :return job name:
    """
    return job_arn[job_arn.rindex("/") + 1:]


def _list_to_dict(
        arg_list: List[Dict[str, Any]], dict_key_attr: str
) -> Dict[Any, Dict]:
    """
    List to Dict
    :param arg_list:
    :param dict_key_attr:
    :return:
    """
    return {o[dict_key_attr]: o for o in arg_list}


def ensure_min_length(argument: str, min_length: int) -> str:
    """
    Add 0's to fulfill min length
    :param argument:
    :param min_length:
    :return:
    """
    if len(argument) < min_length:
        return f"{argument}_ {'0' * (min_length - len(argument))}"
    return argument


def normalize_pipeline_name(name: str, name_max_len: int = 82) -> str:
    """
    max len checker
    :param name:
    :param name_max_len:
    :return:
    """
    name_len = len(name)
    if name_len > name_max_len:
        logging.getLogger(__name__).info(
            'Provided pipeline name "%s" is too long (%d symbols, max allowed: 82). It will be truncated.',
            name,
            name_len,
        )
        name = name[:name_max_len]
    return name


def _generate_data_capture_config(
        s3_destination_prefix: str,
        sampling_percentage: int = 100,
) -> Dict[str, Any]:
    """
    Create Data Capture config from params
    :param s3_destination_prefix:
    :param sampling_percentage:
    :return:
    """
    return {
        "EnableCapture": True,
        "InitialSamplingPercentage": sampling_percentage,
        "DestinationS3Uri": s3_destination_prefix,
        "CaptureOptions": [
            {"CaptureMode": "Input"},
            {"CaptureMode": "Output"},
        ],  # both by default
        "CaptureContentTypeHeader": {"CsvContentTypes": ["text/csv"]},
    }


def create_pipeline(pipeline_name: str, sm_session: Session, steps: list, pipeline_params: list) -> Pipeline:
    """
    Create pipeline using list of steps, generated as a result of compose_pipeline function
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


def compose_pipeline(sm_session: Session, role: str, config_yml_path: str, processing_step_name: str = None,
                     training_step_name: str = None, image_uri: str = None, notebook_path: str = None,
                     hyperparams_file=None) -> list:
    """
    Compose list of pipeline steps.
    To include processing/training step define processing/training_step_name, otherwise ignore ;)
    Args:
        sm_session: sagemaker session
        role: role arn
        config_yml_path: local path of notebook yml configs
        processing_step_name: name of the processing step, IF none -> do not include processing step
        training_step_name: name of the training step, IF none -> skip training step creation
        image_uri: image uri of pushed image to sagemaker
        notebook_path: local path of notebook yml configs
        hyperparams_file: local path of hyperparameters file

    Returns:
        list of composed steps
    """
    pipeline_steps = []
    if processing_step_name:
        processing_step = ProcessingHelper(processing_step_name=processing_step_name,
                                           sagemaker_session=sm_session,
                                           notebook_path=notebook_path,
                                           role=role,
                                           nb_config_path=config_yml_path).create_processing_step()
        pipeline_steps.append(processing_step)

    if training_step_name:
        training_step = TrainingHelper(train_step_name=training_step_name,
                                       sagemaker_session=sm_session,
                                       image_uri=image_uri,
                                       input_data_uri=f's3://{sm_session.default_bucket()}/abalone_data/train',
                                       validation_data_uri=f's3://{sm_session.default_bucket()}/abalone_data/test',
                                       role=role,
                                       nb_config_path=config_yml_path,
                                       hyperparams_file=hyperparams_file).create_training_step()

        pipeline_steps.append(training_step)

    return pipeline_steps

