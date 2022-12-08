import string
import unittest
import random

from mlops_utilities import helpers
from mlops_utilities.actions import upsert_pipeline, run_pipeline


class TestPackageActions(unittest.TestCase):

    @unittest.skip("FIXME")
    def test_upsert_pipeline(self):
        upsert_pipeline(
            pipeline_module='pipelines',
            pipeline_package='training_pipeline',
            pipeline_name='test_pipeline',
            config_type='training_pipeline.defaults',
            role='arn:aws:iam::311638508164:role/AmazonSageMaker-ExecutionRole',
            dryrun=True
        )

    def test_run_pipeline(self):
        run_pipeline(
            pipeline_name='test_pipeline',
            execution_name_prefix='test_pipeline',
            pipeline_params={
                'RegisterModel': False,
                "InputDataS3Uri": f"s3://mlops-sagemaker-project/abalonedata/data.csv",
                "InputLabelS3Uri": f"s3://mlops-sagemaker-project/abalonelabels/data.csv",
            },
            dryrun=True
        )


class TestHelpers(unittest.TestCase):
    def test_convert_param_dict_to_key_value_list_wrong_input(self):
        with self.assertRaises(AttributeError):
            helpers.convert_param_dict_to_key_value_list(None)

    def test_convert_param_dict_to_key_value_list_empty_input(self):
        self.assertListEqual(
            helpers.convert_param_dict_to_key_value_list({}),
            [],
        )

    def test_convert_param_dict_to_key_value_list_correct_input(self):
        self.assertListEqual(
            helpers.convert_param_dict_to_key_value_list({
                'key_1': 'v',
                'key_2': 'vv',
                'key_3': '1',
            }),
            [
                {'Key': 'key_1', 'Value': 'v'},
                {'Key': 'key_2', 'Value': 'vv'},
                {'Key': 'key_3', 'Value': '1'},
            ],
        )

    def test_get_value_from_dict(self):
        test_dict = {"regression_metrics": {"mse": {"value": 4.9}}}
        path = ['regression_metrics', 'mse', 'value']
        self.assertEqual(helpers.get_value_from_dict(test_dict, path), 4.9)

    def test_get_model_name(self):
        test_model_arn = 'arn:aws:sagemaker:us-east-1:311638508164:model-package-group/framework-version'
        self.assertEqual(helpers.get_model_name(test_model_arn), 'framework-version')

    def test_get_job_name(self):
        test_job_arn = 'arn:aws:sagemaker:us-east-1:311638508164:processing-job/pipelines-joqqfahmal9e-splitdataset-ikz14ulv8j'
        self.assertEqual(helpers.get_job_name(test_job_arn), 'pipelines-joqqfahmal9e-splitdataset-ikz14ulv8j')

    def test_ensure_min_length(self):
        test_token = ''.join(random.choices(string.ascii_letters, k=15))
        self.assertEqual(helpers.ensure_min_length(test_token, 17), test_token + '_ 00')

    def test_normalize_pipeline_name(self):
        pipeline_test_name = ''.join(random.choices(string.ascii_letters, k=83))
        self.assertEqual(len(helpers.normalize_pipeline_name(pipeline_test_name)), 82)

    def test_generate_data_capture_config(self):
        self.assertEqual(helpers._generate_data_capture_config('test_prefix'),
                         {
                             'EnableCapture': True,
                             'InitialSamplingPercentage': 100,
                             'DestinationS3Uri': 'test_prefix',
                             'CaptureOptions': [{'CaptureMode': 'Input'}, {'CaptureMode': 'Output'}],  # both by default
                             'CaptureContentTypeHeader': {'CsvContentTypes': ['text/csv']},
                         }
        )
