#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ ! -d "$ROOT/vendor/SkillOpt/.git" ]; then
  git clone --depth 1 https://github.com/microsoft/SkillOpt.git "$ROOT/vendor/SkillOpt"
else
  git -C "$ROOT/vendor/SkillOpt" pull --ff-only
fi

rm -rf "$ROOT/docs/skillopt-site"
mkdir -p "$ROOT/docs/skillopt-site"
wget \
  --mirror \
  --page-requisites \
  --adjust-extension \
  --convert-links \
  --no-parent \
  --directory-prefix "$ROOT/docs/skillopt-site" \
  https://microsoft.github.io/SkillOpt/ \
  https://microsoft.github.io/SkillOpt/docs/guideline.html

echo "SkillOpt source and rendered docs refreshed."
