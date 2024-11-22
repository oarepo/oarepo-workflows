#!/bin/bash

PYTHON="${PYTHON:-python3.12}"
OAREPO_VERSION="${OAREPO_VERSION:-12}"

echo "Will run tests with python ${PYTHON} and oarepo version ${OAREPO_VERSION}"

set -e

install_python_package() {
  package_name=$1
  uppercase_package_name=$(echo $package_name | tr '[:lower:]' '[:upper:]' | tr '-' '_')
  pip_package_name=${!uppercase_package_name}   # dereference the variable if possible
  pip_package_name=${pip_package_name:-$package_name}
  pip install -U $pip_package_name
}

BUILDER_VENV=.venv-builder
TESTS_VENV=.venv-tests

if test -d $BUILDER_VENV ; then
	rm -rf $BUILDER_VENV
fi
curl -L -o forked_install.sh https://github.com/oarepo/nrp-devtools/raw/main/tests/forked_install.sh

$PYTHON -m venv $BUILDER_VENV
. $BUILDER_VENV/bin/activate
pip install -U setuptools pip wheel
install_python_package oarepo-model-builder
install_python_package oarepo-model-builder-drafts
install_python_package oarepo-model-builder-workflows

if test -d thesis ; then
  rm -rf thesis
fi
oarepo-compile-model ./tests/thesis.yaml --output-directory ./thesis -vvv

if test -d $TESTS_VENV ; then
	rm -rf $TESTS_VENV
fi
$PYTHON -m venv $TESTS_VENV
. $TESTS_VENV/bin/activate
pip install -U setuptools pip wheel
pip install "oarepo[tests]==${OAREPO_VERSION}.*"
sh forked_install.sh invenio-records-resources
sh forked_install.sh invenio-requests
sh forked_install.sh invenio-drafts-resources
pip install -e "./thesis[tests]"
pip install -e .

pytest ./tests