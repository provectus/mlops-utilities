#!/usr/bin/env bash
if [[ `git status --porcelain` ]]; then
    echo "There are uncommited changes"
	exit 1
fi
new_version=`poetry version -n -s --dry-run patch`
echo $new_version
# tag release version
#git tag $new_version
# increment version
#cat version | awk '{split($$0, a, "."); print a[1]"."a[2]"."a[3]+1}' > version.new
#mv version.new version
# snapshot version
#printf `cat version`
# commit
#git commit -am "[skip ci] Update to new snapshot version"
# push
#git push origin HEAD:${CI_COMMIT_BRANCH}
#git push --tags