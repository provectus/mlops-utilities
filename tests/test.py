import unittest

from mlops_utilities import helpers
from mlops_utilities.actions import upsert_pipeline, run_pipeline


class TestPackageActions(unittest.TestCase):

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
