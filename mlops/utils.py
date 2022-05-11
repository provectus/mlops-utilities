import json
import boto3
import logging
from pathlib import Path
from omegaconf import OmegaConf
from botocore.client import BaseClient

logger = logging.getLogger(__name__)


def get_datetime_str(arg_dt):
    return arg_dt.strftime('%Y-%m-%d-%H-%M-%S')


def param_dict_to_nv_list(arg_dict):
    return [
        {'Name': k, 'Value': v}
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


def get_metrics(s3_uri):
    s3_client = boto3.client('s3')
    bucket, key = s3_uri.replace("s3://", "").split("/", 1)
    s3_response_object = s3_client.get_object(Bucket=bucket, Key=key)

    return json.loads(s3_response_object['Body'].read().decode('utf-8'))


def get_conf(mod_pipe, pipeline_module, pipeline_role, args):
    default_conf_path = Path(mod_pipe.__file__).parent / (pipeline_module + '.defaults.yml')
    default_conf = OmegaConf.load(default_conf_path)
    arg_conf = OmegaConf.create({'pipeline': {'role': pipeline_role}})
    override_arg_conf = OmegaConf.from_dotlist(args)
    return OmegaConf.merge(default_conf, arg_conf, override_arg_conf)


def truncate_pipeline_name(name: str) -> str:
    """
    Workaround for the weird error we faced while creating/updating a pipeline:
        botocore.exceptions.ClientError: An error occurred (ValidationException) when calling the CreatePipeline
        operation: [string "<pipeline-name>" is too long (length: xxx, maximum allowed: 82)]

    Why 82? Not sure, don't know.
    """
    magic_number = 82
    name_len = len(name)
    if name_len > magic_number:
        logger.info(
            'Provided pipeline name "%s" is too long (%d symbols, max allowed: 82). It will be truncated.',
            name,
            name_len
        )
        name = name[:magic_number]
        logger.info('Updated pipeline name is: "%s"', name)
    return name
