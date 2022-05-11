minor_version_up:
	# increment version
	cat version | awk '{split($$0, a, "."); print a[1]"."a[2]"."a[3]+1}' > version.new
	mv version.new version
	# snapshot version
	printf `cat version`

build_package: minor_version_up
	# login
	aws codeartifact login --tool twine --repository pypi-store --domain ${DOMAIN_NAME} --domain-owner ${DOMAIN_OWNER}
	pip install twine
	export PACKAGE_VERSION=`cat version` && python setup.py bdist_wheel
	twine upload --repository codeartifact dist/mlops-"`cat version`"-py3-none-any.whl

setup_pip:
	pip config set global.index-url https://aws:"`aws codeartifact get-authorization-token --domain ${DOMAIN_NAME} --domain-owner ${DOMAIN_OWNER} --query authorizationToken --output text`"@${DOMAIN_NAME}-${DOMAIN_OWNER}.d.codeartifact.${AWS_REGION}.amazonaws.com/pypi/pypi-store/simple/
