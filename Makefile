test:
	# TODO simplify for local runs
	poetry run pytest tests/test.py --junitxml=report.xml

build:
	poetry build

publish:
	poetry publish

minor_version_up:
	poetry version -n -s minor

patch_version_up:
	./bump_version.sh
	git push origin HEAD:${CI_COMMIT_BRANCH}
	git push --tags

configure_git:
	git config --global user.email ${GITLAB_USER_EMAIL}
	git config --global user.name ${GITLAB_USER_NAME}
	git remote set-url origin https://oauth2:${GITLAB_TOKEN}@gitlab.provectus.com/${CI_PROJECT_PATH}.git