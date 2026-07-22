FROM mcr.microsoft.com/devcontainers/python:3.14

# uv, copied as a static binary (matches astral's own recommended devcontainer pattern) —
# no curl/install-script needed at build time.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Rename the base image's pre-created non-root user/group to something generic — this
# devcontainer is deliberately editor-agnostic end to end, not just at the tool level. Same
# UID/GID, just relabeled, so this doesn't change any of the permission behavior already
# verified to work.
RUN old_user=$(id -nu 1000) \
    && old_group=$(id -ng 1000) \
    && usermod -l dev -d /home/dev -m "$old_user" \
    && groupmod -n dev "$old_group"

USER dev

# The workspace folder is bind-mounted from the host over 9p (WSL2's Windows-drive
# bridge), which is extremely slow for many-small-file workloads - homeassistant alone
# installs tens of thousands of files (source for every built-in integration). Placing
# .venv on the container's own native filesystem instead of the bind-mounted workspace
# avoids that entirely. Matches the pattern in home-assistant/core's own Dockerfile.dev.
ENV VIRTUAL_ENV="/home/dev/.venv"
ENV UV_PROJECT_ENVIRONMENT=$VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
