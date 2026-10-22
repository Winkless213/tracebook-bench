ARG NODE_IMAGE=node:24-bookworm-slim
FROM ${NODE_IMAGE}
ARG NPM_REGISTRY=https://registry.npmjs.org

RUN apt-get update \
  && apt-get install -y --no-install-recommends bash ca-certificates curl git ripgrep procps \
     python3 python3-venv python3-pip \
  && rm -rf /var/lib/apt/lists/*
RUN npm config set registry ${NPM_REGISTRY} \
  && npm install -g --ignore-scripts @earendil-works/pi-coding-agent@1.1.0

RUN git config --system user.name "bench" \
  && git config --system user.email "bench@localhost" \
  && git config --system init.defaultBranch main \
  && git config --system --add safe.directory '*'

WORKDIR /workspace
