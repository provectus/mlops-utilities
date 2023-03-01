"""image creation step"""
import subprocess


class ImageHelper:

    def __init__(self, local_image_name: str, role: str, account_id: str, region: str):

        self.img_name = local_image_name
        self.role = role
        self.account_id = account_id
        self.region = region

    def _run_shell_cmd(self, cmd: str, error_msg: str):
        """

        Args:
            cmd: terminal command
            error_msg: error message
        """
        try:
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        except subprocess.CalledProcessError as exc:
            raise ImageHelperError(f'ImageHelper: {error_msg}') from exc

    def tag_image(self):
        """
            assign tag to local image, usually looks like that <account_id>.dkr.ecr.<region>.amazonaws.com/<img>:<img>
        """
        tagged_img = f'{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{self.img_name}:{self.img_name}'
        self._run_shell_cmd(cmd=f"docker tag {self.img_name} {tagged_img}", error_msg=f'Failed to tag local image')
        return tagged_img

    def crate_ecr_repository(self):
        """
            create ecr repository
        """
        self._run_shell_cmd(cmd=f"aws ecr create-repository --repository-name {self.img_name}",
                            error_msg='Failed to create ecr repository')

    def login_ecr_repository(self):
        """
            login to ecr repository
        """
        self._run_shell_cmd(cmd=f"aws ecr get-login-password --region {self.region} | docker login --username AWS --password-stdin "
                            f"{self.account_id}.dkr.ecr.{self.region}.amazonaws.com/{self.img_name}",
                            error_msg='Failed to login ecr repository')

    def push_docker_image(self, tagged_img):
        """
            push docker image to ecr
        """
        self._run_shell_cmd(cmd=f"docker push {tagged_img}", error_msg='Failed to push local image to ecr')

    def create_sagemaker_image(self):
        """
            create sagemaker image from ecr repository
        """
        self._run_shell_cmd(cmd=f"aws sagemaker create-image --image-name {self.img_name} --role-arn {self.role}",
                            error_msg='Failed to create sagemaker image')

    def create_sagemaker_image_version(self, tagged_img):
        self._run_shell_cmd(cmd=f"aws sagemaker create-image-version --base-image {tagged_img}"
                                f" --image-name {self.img_name}", error_msg='Failed to create image version')


class ImageHelperError(Exception):
    pass
