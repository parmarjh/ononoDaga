#!/bin/sh

set -e

npm run build
aws s3 cp index.html s3://onondaga-e911-dev
aws s3 cp --recursive dist s3://onondaga-e911-dev/dist
