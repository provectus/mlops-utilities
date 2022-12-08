test:
	# TODO simplify for local runs
	"${POETRY_HOME}/bin/poetry" run python3 -m unittest -v

patch_version_up:
	./bump_version.sh
	git push origin HEAD:${CI_COMMIT_BRANCH}
	git push --tags

configure_git:
	git config --global user.email ${GITLAB_USER_EMAIL}
	git config --global user.name ${GITLAB_USER_NAME}
	git remote set-url origin https://oauth2:${GITLAB_TOKEN}@gitlab.provectus.com/${CI_PROJECT_PATH}.git