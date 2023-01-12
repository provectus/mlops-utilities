from typing import List


############################################################
############# DATASETS #####################################
############################################################
class Dataset:
    """
        A definition of a dataset that can be used as input or output of a pipeline step.
    """
    pass


def file_dataset(path: str) -> Dataset:
    """
    Creates a definition of the dataset represented by files located 
    in the specified directory.

    Args:
        path (str): the path of the directory that contains the dataset files.

    Returns:
        Dataset: the dataset definition object.
    """
    raise NotImplementedError()


############################################################
############# MODELS #######################################
############################################################
class Model:
    """
        A definition of a model that can be produced or consumed by a pipeline step.
    """
    pass


def file_model(path: str) -> Model:
    """
    Creates a definition of the model represented by content of the specified directory.

    Args:
        path (str): the path of the directory that contains the model files.

    Returns:
        Model: the model definition object.
    """
    raise NotImplementedError()


############################################################
############# METRICS ######################################
############################################################
class MetricsSchema:
    """
    A schema of metrics files.
    """
    pass


class Metrics:
    """
    A definition of a metric collection that can be produced by a pipeline step.
    """
    pass


def file_metrics(path: str, schema: MetricsSchema) -> Metrics:
    """
    Creates a definition of metrics represented by content of the specified directory
    with the specified schema.

    Args:
        path (str): the path of the directory that contains the metric files.
        schema (MetricsSchema): the schema of the metrics files.

    Returns:
        Metrics: the metrics definition object.
    """
    pass


############################################################
############# ENVIRONMENTS #################################
############################################################
class Environment:
    """
        A definition of an environment that can be used to run a code, for example:
        * jobs,
        * model inference requests.
    """
    pass


############################################################
############# PIPELINE STEPS ###############################
############################################################

class Step:
    """
        A definition of a pipeline step.
    """
    pass


class Job(Step):
    """
        A definition of a pipeline step that runs a job.
    """
    pass


def train_notebook_step(
        code: str, 
        env: Environment, 
        input_datasets: List[Dataset], 
        output_model: Model,
        output_metrics: List[Metrics] = None) -> Job:
    """
    Creates a definition of a pipeline step that runs a Jupyter notebook to train a model.
    
    Args:
        code (str): the path to ipynb notebook file.
        env (Environment): the environment that defines required dependencies (python packages) 
            to run the notebook in.
        input_datasets (List[Dataset]): the datasets that will be used
            as input by the notebook.
        output_model (Model): the model that will be produced by the notebook.
        output_metrics (List[Metrics]): the metrics that will be produced by the notebook.

    Returns:
        Job: the pipeline step definition object.
    """
    raise NotImplementedError()


def inference_notebook_step(
        code: str,
        env: Environment,
        input_dataset: Dataset,
        model: Model,
        output_dataset: Dataset) -> Job:
    """
    Creates a definition of a pipeline step that runs a Jupyter notebook to make predictions.
    
    Args:
        code (str): the path to ipynb notebook file.
        env (Environment): the environment that defines required dependencies (python packages) 
            to run the notebook in.
        input_dataset (Dataset): the dataset that will be used as input by the notebook.
        model (Model): the model that will be used by the notebook.
        output_dataset (Dataset): the dataset that will be produced by the notebook.

    Returns:
        Job: the pipeline step definition object.
    """
    raise NotImplementedError()


############################################################
############# PIPELINES ####################################
############################################################
class Pipeline:
    """
        A definition of a pipeline.
        In general case a pipeline is a collection of steps that can have
        dependencies on each other and form a DAG.
        Pipeline can have designated inputs and outputs that are taken from 
        constituent steps.
        Pipeline can have parameters that are used in its step definitions.
        There are several subtypes of pipelines:
        * model training pipeline that takes one or more datasets as input 
            and produces a model as output.
        * model inference pipeline that takes one or more models as input

    """
    pass


def training_pipeline(
        steps: List[Step]) -> Pipeline:
    """
    Creates a definition of a model training pipeline.

    Args:
        steps (List[Job]): the steps that are part of the pipeline.

    Returns:
        Pipeline: the pipeline definition object.
    """
    raise NotImplementedError()