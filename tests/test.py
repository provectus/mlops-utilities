import unittest
from mlops_sm import helpers
from mlops_sm.actions import upsert_pipeline
from mlops_sm.actions import run_pipeline

class TestPackageActions(unittest.TestCase):
    def test_upsert_pipeline(self):
        upsert_pipeline(
            pipeline_module='pipeline',
            pipeline_package='tests',
            pipeline_name='test_pipeline',
            pipeline_tags={
                'key_1': 'val_1',
                'key_2': 'val_2',
            },
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
