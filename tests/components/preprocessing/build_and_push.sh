image="predict-flight-delay/components/preprocessing"
image_tag="${1:-latest}"
include_latest_image_tag="${2:-false}"

# Get the account number associated with the current IAM credentials
account=$(aws sts get-caller-identity --query Account --output text)

if [ $? -ne 0 ]
then
    exit 255
fi

region=$(aws configure get region)
region=${region:-us-east-1}

fullname="${account}.dkr.ecr.${region}.amazonaws.com/${image}:${image_tag}"

# If the repository doesn't exist in ECR, create it.
aws ecr describe-repositories --repository-names "${image}" > /dev/null 2>&1

if [ $? -ne 0 ]
then
    aws ecr create-repository --repository-name "${image}" > /dev/null
fi

# Use https://github.com/awslabs/amazon-ecr-credential-helper
# instead of
# $(aws ecr get-login --region ${region} --no-include-email)

# Build the docker image locally with the image name and then push it to ECR
# with the full name.
docker build -t ${image} .

docker tag ${image} ${fullname}
docker push ${fullname}

if [[ "$include_latest_image_tag" == "true" ]]; then
  fullname="${account}.dkr.ecr.${region}.amazonaws.com/${image}:latest"
  docker tag ${image} ${fullname}
  docker push ${fullname}
fi
