def environment_from_sagemaker_kernel_info(kernel_name: str) -> Environment:
    """
    Creates an environment definition that will match one of kernels provided 
        by built-in SageMaker Studio images.

    Args:
        kernel_name (str): the name of the SageMaker Studio kernel 
            as it is provided by the notebook metadata.

    Returns:
        Environment: the environment definition object.
    """
    raise NotImplementedError()