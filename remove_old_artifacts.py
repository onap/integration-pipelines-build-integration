#!/usr/bin/env python
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

import os
import shutil
import logging

import requests
from pygerrit2 import GerritRestAPI

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s",
                    level=logging.INFO)

logger = logging.getLogger("clean_repository")
rest = GerritRestAPI(url='https://gerrit.onap.org/r/')
PROJECT = "so"
GITLAB_PROJECT_ID = os.getenv('CI_PROJECT_ID', "24365265")
GITLAB_BASE_URL = os.getenv('CI_API_V4_URL', "https://gitlab.com/api/v4")
CI_HEADERS = { 'PRIVATE-TOKEN': os.getenv('CI_private_token',
                                              "won't work") }

open_reviews = []
stale_reviews = []
results_to_delete = []
reviews_max_patchset = {}
reviews_several_patchsets = []

repositories_url = "{}/projects/{}/registry/repositories/".format(
    GITLAB_BASE_URL, GITLAB_PROJECT_ID)
repositories = requests.get(repositories_url, headers=CI_HEADERS).json()


def tag_url(repository, tag):
    return "{}/projects/{}/registry/repositories/{}/tags/{}".format(
        GITLAB_BASE_URL, GITLAB_PROJECT_ID, repository['id'], tag['name'])

def delete_tag(repository, tag):
    deletion = requests.delete(tag_url(repository, tag), headers=CI_HEADERS)
    logger.info(deletion.text)

changes = rest.get("/changes/?q=project:{}%20status:open".format(PROJECT))
for change in changes:
    open_reviews.append(change['_number'])
changes = rest.get("/changes/?q=age:1mon%20project:{}%20status:open".format(
    PROJECT))
for change in changes:
    stale_reviews.append(change['_number'])

logger.debug("%s reviews opened", len(open_reviews))

for repository in repositories:
    logger.info("working on repository %s", repository['name'])
    tags = requests.get(
        "{}/projects/{}/registry/repositories/{}/tags?per_page=100".format(
            GITLAB_BASE_URL, GITLAB_PROJECT_ID, repository['id'])).json()
    for tag in tags:
        review = int(tag['name'].split('-')[0])
        patchset = int(tag['name'].split('-')[1])
        if review in stale_reviews:
            logger.info("review %6s is in stale_reviews, deleting %s",
                         review, tag['name'])
            delete_tag(repository, tag)
        else:
            if review not in open_reviews:
                logger.info(
                    "review %6s is in NOT open_reviews, deleting %s",
                        review, tag['name'])
                delete_tag(repository, tag)
            else:
                logger.debug(
                    "review %6s is in open_reviews, looking for most recent patchset",
                    review)
                if review in reviews_max_patchset:
                    logger.debug("review %6s has several patchsets, finding max",
                                    review)

                    if review not in reviews_several_patchsets:
                        logger.debug(
                            "review %6s has several patchsets, adding to list",
                                review)
                        reviews_several_patchsets.append(review)
                    if reviews_max_patchset[review] < patchset:
                        logger.debug(
                            "current max patchset (%2s) for review %6s is smaller than this one: %2s",
                                reviews_max_patchset[review], review, patchset)
                        reviews_max_patchset[review] = patchset
                else:
                    logger.debug("patchset %2s for review %6s is the first one",
                                    patchset, review)
                    reviews_max_patchset[review] = patchset

    for tag in tags:
        logger.debug("tag: %s", tag['name'])
        review = int(tag['name'].split('-')[0])
        patchset = int(tag['name'].split('-')[1])
        logger.debug("review: %6s", review)
        logger.debug("patchset: %2s", patchset)
        if review in reviews_several_patchsets:
            logger.debug(
                "review %6s has several patchset, keeping only the most recent",
                    review)
            if patchset < reviews_max_patchset[review]:
                logger.info(
                    "current patchset (%2s) of review %6s is smaller than most recent (%2s), deleting %s",
                        patchset, review, reviews_max_patchset[review],
                        tag['name'])
                delete_tag(repository, tag)
