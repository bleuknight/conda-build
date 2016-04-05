import os
import subprocess
import sys

import pytest

thisdir = os.path.dirname(os.path.realpath(__file__))
metadata_dir = os.path.join(thisdir, "test-recipes/metadata")
fail_dir = os.path.join(thisdir, "test-recipes/fail")


def is_valid_dir(parent_dir, dirname):
    valid = os.path.isdir(os.path.join(parent_dir, dirname))
    valid &= not dirname.startswith("_")
    valid &= ('osx_is_app' != dirname or sys.platform == "darwin")
    return valid


@pytest.fixture(params=[dirname for dirname in os.listdir(metadata_dir) if is_valid_dir(metadata_dir, dirname)])
def recipe(request):
    cwd = os.getcwd()
    os.chdir(metadata_dir)
    def fin():
        os.chdir(cwd)
    request.addfinalizer(fin)
    return os.path.join(metadata_dir, request.param)


def test_recipe_builds(recipe):
    env = dict(os.environ)
    # These variables are defined solely for testing purposes,
    # so they can be checked within build scripts
    env["CONDA_TEST_VAR"] = "conda_test"
    env["CONDA_TEST_VAR_2"] = "conda_test_2"

    cmd = 'conda build --no-anaconda-upload {}'.format(recipe)
    subprocess.check_call(cmd.split(), env=env)


@pytest.mark.skipif(sys.platform=="win32",
                    reason="No windows symlinks")
def test_symlink_fail():
    cmd = 'conda build --no-anaconda-upload {}'.format(os.path.join(fail_dir, "symlinks"))
    process = subprocess.Popen(cmd.split(),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    error = error.decode('utf-8')
    assert error.count("Error") == 6

@pytest.mark.skipif(sys.platform=="win32",
                    reason="Windows doesn't show this error")
def test_broken_conda_meta():
    cmd = 'conda build --no-anaconda-upload {}'.format(os.path.join(fail_dir, "conda-meta"))
    process = subprocess.Popen(cmd.split(),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    error = error.decode('utf-8')
    assert "Error: Untracked file(s) ('conda-meta/nope',)" in error

def test_recursive_fail():
    cmd = 'conda build --no-anaconda-upload {}'.format(os.path.join(fail_dir, "recursive-build"))
    process = subprocess.Popen(cmd.split(),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    error = error.decode('utf-8')
    assert "recursive-build2" in error

def test_jinja_typo():
    cmd = 'conda build --no-anaconda-upload {}'.format(os.path.join(fail_dir, "source_git_jinja2_oops"))
    process = subprocess.Popen(cmd.split(),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    error = error.decode('utf-8')
    assert "'GIT_DSECRIBE_TAG' is undefined" in error
