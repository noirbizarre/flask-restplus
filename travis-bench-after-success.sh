#!/usr/bin/env bash
#
# Perform benchmark and compare with base branch results.
# Only here for information purpose
# Adapted from:
#   - http://sunjay.ca/2017/04/27/rust-benchmark-comparison-travis
#   - https://beachape.com/blog/2016/11/02/rust-performance-testing-on-travis-ci/

set -e
set -x

# The Travis environment variables behave like so:
# TRAVIS_BRANCH
#   - if PR build, this is the pr base branch
#   - if push build, this is the branch that was pushed
# TRAVIS_PULL_REQUEST_BRANCH
#   - if PR build, this is the "target" of the pr, i.e. not the base branch
#   - if push build, this is blank
#
# Example:
# You open a PR with base `master`, and PR branch `foo`
# During a PR build:
#     TRAVIS_BRANCH=master
#     TRAVIS_PULL_REQUEST_BRANCH=foo
# During a push build:
#     TRAVIS_BRANCH=foo
#     TRAVIS_PULL_REQUEST_BRANCH=

# Only run on branches
if [ "${TRAVIS_PULL_REQUEST_BRANCH:-$TRAVIS_BRANCH}" != "master" ]; then
    REMOTE_URL="$(git config --get remote.origin.url)"

    # Clone the repository fresh..for some reason checking out master fails
    # from a normal PR build's provided directory
    cd ${TRAVIS_BUILD_DIR}/..
    git clone ${REMOTE_URL} "${TRAVIS_REPO_SLUG}-bench"
    cd  "${TRAVIS_REPO_SLUG}-bench"

    # Bench the pull request base or master
    if [ -n "$TRAVIS_PULL_REQUEST_BRANCH" ]; then
      git checkout -f "$TRAVIS_BRANCH"
    else # this is a push build
      # This could be replaced with something better like asking git which
      # branch is the base of $TRAVIS_BRANCH
      git checkout -f master
    fi

    # Install dependencies in case of change between commits
    pip install -e .[ci]

    # Perform benchmark and save result for comparison
    inv benchmark --max-time 4 --save

    # Bench the current commit that was pushed
    git checkout -f "${TRAVIS_PULL_REQUEST_BRANCH:-$TRAVIS_BRANCH}"

    # Install dependencies in case of change between commits
    pip install -e .[ci]

    # Perform benchmark and compare with previous result
    inv benchmark --max-time 4 --compare

fi
