# Open-CE Automatic Releases

This document describes how automatic releases work for the
[Open-CE Organization](https://github.com/open-ce).

- [Open-CE Automatic Releases](#open-ce-automatic-releases)
  - [Open-CE Release Process](#open-ce-release-process)
  - [Automatic Release Source Code](#automatic-release-source-code)
    - [Python Code](#python-code)
      - [Release Script](#release-script)
    - [Workflows](#workflows)
      - [PR Workflow](#pr-workflow)
      - [Merge Workflow](#merge-workflow)

## Open-CE Release Process

The process for an Open-CE Release is as follows:

1. A release is triggered if the  `git_tag_for_env` field has been modified within the
   [envs/opence-env.yaml](../envs/opence-env.yaml) file.
1. All env files referenced within the [envs/opence-env.yaml](../envs/opence-env.yaml)
   file will be verified to ensure a matching `git_tag_for_env`.
1. All feedstocks referenced within the [envs/opence-env.yaml](../envs/opence-env.yaml)
   file will be tagged with this new tag.
   - If this is a bug fix, meaning that there was already a tag in this branch,
     the old tag will be used to determine which branches of the feedstocks to tag.
1. A draft release is created in the Open-CE repo that must be manually verified and released.

## Automatic Release Source Code

### Python Code

#### Release Script

Most of the work for the release happens in the
[create_opence_release.py script](https://github.com/open-ce/open-ce-builder/blob/main/git_tools/create_opence_release.py).

### Workflows

The automatic release infrastructure is primarily made up of two workflows.
One that is triggered on PRs and one that is triggered on merges.

#### PR Workflow

The [PR workflow](../.github/workflows/opence-pr.yml)
will perform a "release dry run". Meaning that it will do all steps for a release except push
anything upstream.

#### Merge Workflow

The [merge workflow](../.github/workflows/opence-merge.yml)
will, if needed, perform a full release.
