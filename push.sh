#!/bin/bash

docker buildx build --platform linux/amd64,linux/arm64 -t ghcr.io/aglide100/paperless-ngx . --push
