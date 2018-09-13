#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

for recipe in recipes/*/
do
    ./build.py "$recipe"
done
