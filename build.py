#!/usr/bin/env python
from argparse import ArgumentParser
from datetime import datetime
from functools import partial
from pathlib import Path
from subprocess import check_output
from subprocess import run
import os

import yaml


root = Path(__file__).parent.resolve()


def main():
    parser = ArgumentParser()
    parser.add_argument('recipe_dir', type=Path)
    parser.add_argument('py_ver')
    args = parser.parse_args()
    recipe_dir = args.recipe_dir.resolve()

    # Donwload source code
    src_dir = git_clone(recipe_dir)

    # Set environment variables for recipe meta.yaml
    os.environ['RECIPE_PKG_VER'] = get_pkg_ver(src_dir)
    os.environ['RECIPE_SRC_DIR'] = os.path.relpath(src_dir, recipe_dir)

    # Build package
    pkg_file = conda_build(recipe_dir, args.py_ver)

    # Only upload to Anaconda Cloud when using CI
    # This check works for most CIs including Travis CI and AppVeyor
    if os.environ['CI'].lower() == 'true':
        # Test with my personal account for now
        anaconda_upload(pkg_file, 'qobilidop')


def git_clone(recipe_dir):
    with (recipe_dir / 'source.yaml').open() as f:
        source = yaml.load(f)
    repo_dir = root / 'repo'
    repo_dir.mkdir(exist_ok=True)
    src_dir = repo_dir / recipe_dir.name
    if not src_dir.exists():
        print(f'\nDownloading {recipe_dir.name} source code')
        run([
            'git', 'clone',
            '-b', source['git_rev'],
            '--depth', '1',
            source['git_url'], str(src_dir)
        ], check=True)
    return src_dir


def get_pkg_ver(src_dir):
    run_cmd = partial(check_output, shell=True, cwd=src_dir, text=True)
    # This could be multiple lines (on Windows somehow)
    # We just need the last one
    pkg_ver = run_cmd('python setup.py --version').split()[-1]
    pkg_ver = pkg_ver.strip()
    utime = run_cmd('git log -1 --pretty=format:%ct')
    chash = run_cmd('git log -1 --pretty=format:%h')
    stamp = datetime.fromtimestamp(int(utime)).strftime('%Y%m%d%H%M%S')
    pkg_ver += f'_{stamp}_{chash}'
    print(f'Package version: {pkg_ver}')
    return pkg_ver


def conda_build(recipe_dir, py_ver):
    print(f'\nBuilding {recipe_dir.name} in Python {py_ver}')
    build_cmd = [
        'conda', 'build',
        '--python', py_ver,
        '--old-build-string',
        str(recipe_dir)
    ]
    run(build_cmd, check=True)
    # Be careful with the trailing newline
    pkg_file = check_output(build_cmd + ['--output'], text=True).strip()
    return pkg_file


def anaconda_upload(pkg_file, user):
    print(f'\nUploading {pkg_file}')
    run([
        'anaconda',
        '-t', os.environ['CONDA_UPLOAD_TOKEN'],
        'upload',
        '-u', user,
        '-l', 'dev',
        '--skip',
        str(pkg_file)
    ], check=True)


if __name__ == '__main__':
    main()
