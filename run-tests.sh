#!/bin/bash

set -e

export PIP_EXTRA_INDEX_URL=https://gitlab.cesnet.cz/api/v4/projects/1408/packages/pypi/simple
export UV_EXTRA_INDEX_URL=https://gitlab.cesnet.cz/api/v4/projects/1408/packages/pypi/simple

VENV=.venv

if test -d $VENV ; then
	rm -rf $VENV
fi
uv venv
source .venv/bin/activate
uv lock --upgrade
uv sync --all-extras
#editable_install oarepo-model-alt4
#editable_install oarepo-global-search
#editable_install pytest-oarepo
#editable_install oarepo-ui
#editable_install oarepo-rdm

#. $TESTS_VENV/bin/activate
#pip install -U setuptools pip wheel
#pip install "oarepo[tests,rdm]==${OAREPO_VERSION}.*"
#pip install -e "./thesis[tests]"
#pip install -e .

#pytest ./tests