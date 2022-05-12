from sagemaker import Session
from omegaconf.dictconfig import DictConfig
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.steps import ProcessingStep


def get_pipeline(
        sm_session: Session,
        pipeline_name: str,
        conf: DictConfig,
        component_versions: str = None,
) -> Pipeline:

    return Pipeline(
        name=pipeline_name,
        steps=[
            ProcessingStep(
                name=conf.step.name,
                step_args={'k': 'v'}
            )
        ],
        sagemaker_session=sm_session
    )
