#!/bin/bash
#   Copyright 2023 Orange, Deutsche Telekom AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

set -o errexit
set -o nounset
set -o pipefail

echo "Clone xtesting repository"
git clone "${XTESTING_GIT}"
cd xtesting/smoke-usecases-pythonsdk

echo "Build an image with gerrit patchset's pythonsdk-tests version"
CI_REGISTRY_IMAGE_TAG=${GERRIT_REVIEW}-${GERRIT_PATCHSET}
PYTHONSDK_TESTS_GERRIT_CHANGE_TAG="refs/changes/${GERRIT_REVIEW: -2}/${GERRIT_REVIEW}/${GERRIT_PATCHSET}"
docker build --build-arg ONAP_TESTS_TAG=$PYTHONSDK_TESTS_GERRIT_CHANGE_TAG -t $CI_REGISTRY_IMAGE:$CI_REGISTRY_IMAGE_TAG -f ./docker/Dockerfile .

echo "Push an image into registry"
docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
docker push $CI_REGISTRY_IMAGE:$CI_REGISTRY_IMAGE_TAG
