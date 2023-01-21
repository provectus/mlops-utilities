import functools
from unittest.mock import MagicMock

from mlops_utilities import helpers
from mlops_utilities.actions import compare_metrics, create_endpoint, update_endpoint


def mock_sagemaker_session(f):
    @functools.wraps(f)
    def mock_sagemaker_session_(*args, **kwargs):
        boto_mock = MagicMock(name="boto_session", region_name="us-east-1")
        sms = MagicMock(
            name="sagemaker_session",
            boto_session=boto_mock,
            boto_region_name="us-east-1",
            config=None,
            local_mode=False,
        )
        return f(*args, sm_client=sms.sagemaker_client, **kwargs)

    return mock_sagemaker_session_


class TestPackageActions:
    endpoint_name = "TestEndpoint"
    test_instance_type = "ml.m5.large"
    test_role = "arn:aws:iam::123456789000:role/AmazonSageMaker-ExecutionRole"

    @mock_sagemaker_session
    def test_get_approved_package(self, **kwargs):
        sm_client = kwargs.pop("sm_client")
        model_package_group_name = "test-model-package-group"
        helpers.get_approved_package(sm_client, model_package_group_name)

    @mock_sagemaker_session
    def test_get_model_location(self, **kwargs):
        sm_client = kwargs.pop("sm_client")
        helpers.get_model_location(sm_client, "test-model-package-group")

    @mock_sagemaker_session
    def test_create_model_from_model_package(self, **kwargs):
        sm_client = kwargs.pop("sm_client")
        model_package_arn = "arn:aws:sagemaker:us-east-1:123456789000:model-package/test-model-package-group/1"
        helpers.create_model_from_model_package(
            sagemaker_client=sm_client,
            model_name="model",
            model_package_arn=model_package_arn,
            execution_role=self.test_role,
            tags=None,
        )

    @mock_sagemaker_session
    def test_compare_metrics(self, **kwargs):
        sm_client = kwargs.pop("sm_client")
        endpoint_config_description = sm_client.describe_endpoint_config(
            EndpointConfigName=self.endpoint_name
        )
        evaluate_s3 = ""
        metric_path = "regression_metrics/mse/value"
        compare_metrics(
            sagemaker_client=sm_client,
            endpoint_config_description=endpoint_config_description,
            model_statistics_s3_uri=evaluate_s3,
            metric=metric_path,
            dryrun=True,
        )

    @mock_sagemaker_session
    def test_create_endpoint(self, **kwargs):
        sm_client = kwargs.pop("sm_client")
        create_endpoint(
            model_package_arn="arn:aws:sagemaker:us-east-1:123456789000:model-package/test-model-package-group/1",
            sagemaker_session=sm_client,
            instance_count=1,
            instance_type=self.test_instance_type,
            endpoint_name=self.endpoint_name,
            data_capture_config=None,
            role=self.test_role,
        )

    @mock_sagemaker_session
    def test_update_endpoint(self, **kwargs):
        sm_client = kwargs.pop("sm_client")
        update_endpoint(
            sagemaker_client=sm_client,
            endpoint_name=self.endpoint_name,
            data_capture_config=None,
            dryrun=True,
        )
