#!/usr/bin/env bash
set -e
# check for uncommited changes
if [[ `git status --porcelain` ]]; then
    git status
    echo "There are uncommited changes"
	exit 1
fi
# increment version
new_version=`"$POETRY_HOME/bin/poetry" version -n -s patch`
echo "Bumped to new version: $new_version"
# commit changes
git commit -am "[skip ci] Version updated to $new_version"
# tag release version
git tag $new_version
