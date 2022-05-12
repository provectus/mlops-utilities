minor_version_up:
	git config --global user.email ${GITLAB_USER_EMAIL}
	git config --global user.name ${GITLAB_USER_NAME}
	git remote set-url origin https://oauth2:${GITLAB_TOKEN}@gitlab.provectus.com/${CI_PROJECT_PATH}.git
	# tag release version
	git tag --delete `cat version`
	git tag `cat version`
	# increment version
	cat version | awk '{split($$0, a, "."); print a[1]"."a[2]"."a[3]+1}' > version.new
	mv version.new version
	# snapshot version
	printf `cat version`
	# commit
	git commit -am "[skip ci] Update to new snapshot version"
	# push
	git push origin HEAD:${CI_COMMIT_BRANCH}
	git push --tags

setup_pip:
	pip config set global.index-url https://aws:"`aws codeartifact get-authorization-token --domain ${DOMAIN_NAME} --domain-owner ${DOMAIN_OWNER} --query authorizationToken --output text`"@${DOMAIN_NAME}-${DOMAIN_OWNER}.d.codeartifact.${AWS_REGION}.amazonaws.com/pypi/pypi-store/simple/
