"""training step helper"""
import json

from omegaconf import OmegaConf
from sagemaker import Session, TrainingInput
from sagemaker.estimator import Estimator
from sagemaker.workflow.steps import TrainingStep


class TrainingHelper:

    def __init__(self, train_step_name: str, sagemaker_session: Session, image_uri: str, input_data_uri: str,
                 validation_data_uri: str, role: str, nb_config_path: str, hyperparams_file: str = None):

        self.train_step_name = train_step_name
        self.sm_session = sagemaker_session
        self.image_uri = image_uri
        self.input_data_uri = input_data_uri
        self.validation_data_uri = validation_data_uri
        self.role = role
        self.nb_config_path = nb_config_path
        self.hyperparams_file = hyperparams_file

    def _load_nb_config(self):
        """

        Args:
            local path of notebook yml configs
        Returns:
            loaded yml configs
        """
        return OmegaConf.load(self.nb_config_path)

    def create_estimator(self) -> Estimator:
        """
        Returns:
            estimator for training job
        """
        nb_config = self._load_nb_config()
        if self.hyperparams_file:
            with open(self.hyperparams_file, encoding='utf-8') as json_file:
                hyperparams_dict = json.load(json_file)

        return Estimator(
            image_uri=self.image_uri,
            instance_type=nb_config.processing.instance_type,
            instance_count=nb_config.processing.instance_count,
            base_job_name="notebook-train",
            sagemaker_session=self.sm_session,
            role=self.role,
            hyperparameters=hyperparams_dict
        )

    def create_training_step(self) -> TrainingStep:
        """
        Returns:
            training step
        """
        estimator = self.create_estimator()
        return TrainingStep(
            name=self.train_step_name,
            estimator=estimator,
            inputs={
                "train": TrainingInput(
                    s3_data=self.input_data_uri,
                    content_type="text/csv",
                ),
                "validation": TrainingInput(
                    s3_data=self.validation_data_uri,
                    content_type="text/csv",
                ),
            },
        )
