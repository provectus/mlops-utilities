#!/usr/bin/env bash
# check for uncommited changes
if [[ `git status --porcelain` ]]; then
    git status
    echo "There are uncommited changes"
	exit 1
fi
# increment version
new_version=`poetry version -n -s patch`
echo "Bumped to new version: $new_version"
# commit changes
git commit -am "[skip ci] Version updated to $new_version"
# tag release version
git tag "version-$new_version"
