"""processing step helper"""
import os

from omegaconf import OmegaConf
from sagemaker import Session
from sagemaker.processing import FrameworkProcessor, ProcessingInput, ProcessingOutput
from sagemaker.sklearn import SKLearn
from sagemaker.workflow.steps import ProcessingStep

PROCESSING_CONTAINER_DIR = "/opt/ml/processing"


class ProcessingHelper:

    def __init__(self, processing_step_name: str, sagemaker_session: Session, notebook_path: str, role: str,
                 nb_config_path: str):
        self.processing_step_name = processing_step_name
        self.sagemaker_session = sagemaker_session
        self.notebook_path = notebook_path
        self.role = role
        self.nb_config_path = nb_config_path

    def _load_nb_config(self):
        """

        Args:
            local path of notebook yml configs
        Returns:
            loaded yml configs
        """
        return OmegaConf.load(self.nb_config_path)

    def _create_processor(self) -> FrameworkProcessor:
        """
        Returns:
            processor framework
        """
        nb_config = self._load_nb_config()
        return FrameworkProcessor(
            estimator_cls=SKLearn,
            framework_version="0.23-1",
            role=self.role,
            instance_count=nb_config.training.instance_count,
            instance_type=nb_config.training.instance_type,
            sagemaker_session=self.sagemaker_session,
        )

    def create_processing_step(self) -> ProcessingStep:
        """
        Returns:
            sagemaker processing job
        """
        return ProcessingStep(
            self.processing_step_name,
            processor=self._create_processor(),
            inputs=[
                ProcessingInput(
                    input_name="code",
                    source=self.notebook_path,
                    destination=os.path.join(PROCESSING_CONTAINER_DIR, "code"),
                ),
            ],
            outputs=[
                ProcessingOutput(
                    output_name="output-data",
                    source=os.path.join(PROCESSING_CONTAINER_DIR, "output-data"),
                )
            ],
            code=os.path.join(self.notebook_path, "entrypoint.sh")
        )
