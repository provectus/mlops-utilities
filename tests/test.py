import unittest
from mlops_utilities.actions import upsert_pipeline
from mlops_utilities.actions import run_pipeline


class TestPackageActions(unittest.TestCase):
    def test_upsert_pipeline(self):
        upsert_pipeline(
            pipeline_module='pipeline',
            pipeline_package='upsert',
            pipeline_name='test_pipeline',
            pipeline_role='test_role',
            component_versions='latest',
            dryrun=True
        )

    def test_run_pipeline(self):
        run_pipeline(
            pipeline_name='test_pipeline',
            execution_name_prefix='test_pipeline',
            dryrun=True
        )
