import json
import boto3
import logging
from pathlib import Path
from omegaconf import OmegaConf
from botocore.client import BaseClient
from typing import Dict, List


def get_datetime_str(arg_dt):
    return arg_dt.strftime('%Y-%m-%d-%H-%M-%S')


def param_dict_to_nv_list(arg_dict):
    return [
        {'Name': k, 'Value': v}
        for k, v in arg_dict.items()
    ]


def convert_param_dict_to_key_value_list(arg_dict: Dict[str, str]) -> List[Dict[str, str]]:
    """
    Convert python dict to Sagemaker SDK resource tags structure
    where dict key corresponds to "Key", dict value corresponds to "Value".
    :param arg_dict: key-value need to convert to AWS resource tags structure
    :return: list of tags in the following format: [ { "Key": "...", "Value": "..." }, ... ]
    """
    return [
        {'Key': k, 'Value': v}
        for k, v in arg_dict.items()
    ]


def normalize_key(key: str):
    return key.replace('_', '').lower()


def get_model_name(model_arn):
    return model_arn[model_arn.rindex('/') + 1:]


def get_job_name(job_arn):
    return job_arn[job_arn.rindex('/') + 1:]


def get_output_destination(sm, processing_job_arn, output_name):
    pj_output_dict = _list_to_dict(
        sm.describe_processing_job(
            ProcessingJobName=get_job_name(processing_job_arn)
        )['ProcessingOutputConfig']['Outputs'],
        'OutputName'
    )
    return pj_output_dict[output_name]['S3Output']['S3Uri']


def get_model_location(sm, model_name):
    model_desc = sm.describe_model(ModelName=model_name)
    return model_desc['PrimaryContainer']['ModelDataUrl']


def _list_to_dict(arg_list, dict_key_attr):
    return {
        o[dict_key_attr]: o
        for o in arg_list
    }


def ensure_min_length(arg_str, min_length):
    if len(arg_str) < min_length:
        return arg_str + '_' + ('0' * (min_length - len(arg_str)))
    else:
        return arg_str


def get_approved_package(sm: BaseClient, model_package_group_name: str):
    response = sm.list_model_packages(
        ModelApprovalStatus='Approved',
        ModelPackageGroupName=model_package_group_name,
        SortBy='CreationTime',
        SortOrder='Descending',
        MaxResults=1,
    )

    model_packages = response['ModelPackageSummaryList']
    if len(model_packages) == 0:
        error_message = (
            f"No approved ModelPackage found for ModelPackageGroup: {model_package_group_name}"
        )
        raise Exception(error_message)

    return model_packages[0]


def load_json_from_s3(s3_uri: str):
    s3_client = boto3.client('s3')
    bucket, key = s3_uri.replace("s3://", "").split("/", 1)
    s3_response_object = s3_client.get_object(Bucket=bucket, Key=key)

    return json.loads(s3_response_object['Body'].read().decode('utf-8'))


def get_configs(mod_pipe, pipeline_module, args):
    default_conf_path = Path(mod_pipe.__file__).parent / (pipeline_module + '.defaults.yml')
    default_conf = OmegaConf.load(default_conf_path)
    override_arg_conf = OmegaConf.from_dotlist(args)
    return OmegaConf.merge(default_conf, override_arg_conf)


def _normalize_pipeline_name(name: str) -> str:
    name_max_len = 82
    name_len = len(name)
    if name_len > name_max_len:
        logging.getLogger(__name__).info(
            'Provided pipeline name "%s" is too long (%d symbols, max allowed: 82). It will be truncated.',
            name,
            name_len
        )
        name = name[:name_max_len]
    return name
