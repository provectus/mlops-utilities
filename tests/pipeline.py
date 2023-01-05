from sagemaker.workflow.pipeline_context import PipelineSession
from omegaconf.dictconfig import DictConfig
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep


def get_pipeline(sm_session: PipelineSession, pipeline_name: str, conf: DictConfig) -> Pipeline:

    return Pipeline(
        name=pipeline_name,
        steps=[ProcessingStep(name=conf.step.name, step_args={"k": "v"})],
        sagemaker_session=sm_session,
    )
