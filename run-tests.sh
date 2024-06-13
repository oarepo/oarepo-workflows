#!/bin/bash

PYTHON="${PYTHON:-python3.10}"

set -e

OAREPO_VERSION="${OAREPO_VERSION:-12}"

BUILDER_VENV=.venv-builder
TESTS_VENV=.venv-tests

if test -d $BUILDER_VENV ; then
	rm -rf $BUILDER_VENV
fi

if test -d $TESTS_VENV ; then
	rm -rf $TESTS_VENV
fi

$PYTHON -m venv $BUILDER_VENV
. $BUILDER_VENV/bin/activate
pip install -U setuptools pip wheel
pip install -U oarepo-model-builder oarepo-model-builder-drafts

if test -d thesis ; then
  rm -rf thesis
fi
oarepo-compile-model ./tests/thesis.yaml --output-directory thesis -vvv

$PYTHON -m venv $TESTS_VENV
. $TESTS_VENV/bin/activate
pip install -U setuptools pip wheel
pip install "oarepo[tests]==${OAREPO_VERSION}.*"
pip install -e ".[tests]"
pip install -e thesis

