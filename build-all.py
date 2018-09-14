#!/usr/bin/env python
from pathlib import Path
from subprocess import run


root = Path(__file__).parent.resolve()


if __name__ == '__main__':
    for recipe in (root / 'recipes').glob('*'):
        for py_ver in ['2.7', '3.5', '3.6', '3.7']:
            run(['python', 'build.py', str(recipe), py_ver], cwd=root,
                check=True)
