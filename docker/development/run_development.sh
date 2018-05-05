#!/usr/bin/env bash
# # API Star Development Environment Runner
# Runs a minimal Debian based image with latest selected python image.
#
# ## Requires:
# * Docker
# * A Debian based Python Image (https://hub.docker.com/_/python/)
#
# ## Features:
# * Change PYTHON_TAG to change python version
# * Every run creates a new clean container with a different name
# * Every run stops and removes the container when exited automatically
# * You can have several containers running at once (different branches, different pythons...)
#
# ## Parameters
# It accepts one parameter or none and it defaults Latest py36: python:slim-stretch
# e.g. for Py35
# ./docker/development/run_development.sh "python:3.5-slim"
# e.g. for Pypy3 (https://hub.docker.com/_/pypy/)
# ./docker/development/run_development.sh "pypy:3-slimm"
#
# Any Debian based with proper py3 or pypy installed can be used

# Init image
if [ -z ${1+x} ]; then
    PYTHON_IMAGE='python:slim-stretch';
  else
      echo "PYTHON_IMAGE is set to '$1'";
      PYTHON_IMAGE="$1";
fi

read -r -d '' START_COMMAND << EOM
    set -e
    apt-get update > /dev/null && apt-get install -y figlet > /dev/null && figlet "API Star *"
    echo '  ~~~~~~~~~~~~~~~~~~~~~~~~'
    echo '  A smart Web API framework, for Python 3.'
    echo '  LICENCE BASD-3-Clause'
    echo '  Github: https://github.com/encode/apistar'
    echo '  ~~~~~~~~~~~~~~~~~~~~~~~~'
    echo ' '
    echo '* System setup...'
    apt-get update > /dev/null && apt-get install -y build-essential > /dev/null
    echo '... done.'
    cd /apistar;
    echo '* Local env setup...'
    bash ./scripts/setup  > /dev/null;
    echo '... setup done.'
    echo 'echo "* Local env: /apistar/venv"' >> ~/.bashrc
    echo 'echo "* Installed venv packages:"' >> ~/.bashrc
    echo 'echo " "'  >> ~/.bashrc
    echo 'echo "#####################"'  >> ~/.bashrc
    echo 'cd /apistar && ./venv/bin/pip freeze'  >> ~/.bashrc
    echo 'echo "#####################"'  >> ~/.bashrc
    echo 'echo " "'  >> ~/.bashrc
    echo 'echo "~* You can now run tests with ./scripts/tests *~"'  >> ~/.bashrc
    echo 'echo "~* You are all set! Happy coding :) *~"'  >> ~/.bashrc
    echo 'echo " "'  >> ~/.bashrc
    bash
EOM
# Force to have some setuptools config even empty, make them available
if [ ! -f ~/.pip/pip.conf ]; then
    mkdir -p ~/.pip
    touch ~/.pip/pip.conf
fi
if [ ! -f ~/.pypirc ]; then
    touch ~/.pypirc
fi
now=`date +%Y-%m-%d%H%M%S`
name="apistar_development_runner_${PYTHON_IMAGE//:}_${now}"
echo "Launching container with name: ${name}"
docker run --name apistar-dev \
    -v $(pwd):/apistar -v ~/.ssh:$HOME/.ssh -v ~/.pip:$HOME/.pip -v ~/.pypirc:$HOME/.pypirc \
    --name ${name} \
    --rm -it ${PYTHON_IMAGE} \
    bash -c "${START_COMMAND}"
