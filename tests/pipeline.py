from sagemaker import Session
from omegaconf.dictconfig import DictConfig
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep
from sagemaker.workflow.pipeline_context import PipelineSession

from sagemaker.processing import Processor

from sagemaker.image_uris import get_training_image_uri

pipeline_session = PipelineSession()
my_processor = Processor(
    role='arn:aws:iam::311638508164:role/AmazonSageMaker-ExecutionRole',
    image_uri=get_training_image_uri(region='us-east-1',framework='xgboost'),
    instance_type='ml.m5.xlarge',
    instance_count=1,
    sagemaker_session=pipeline_session
)

def get_pipeline(
        sm_session: Session,
        pipeline_name: str,
        conf: DictConfig
) -> Pipeline:

    return Pipeline(
        name=pipeline_name,
        steps=[
            ProcessingStep(
                name=conf.step.name,
                processor=my_processor,
                step_args=my_processor.run(
                    inputs=[],
                    ouputs=[]
                )
            )
        ],
        sagemaker_session=sm_session
    )
