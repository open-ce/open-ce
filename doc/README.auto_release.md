# Open-CE Automatic Releases

This document describes how automatic releases work for the
[Open-CE Organization](https://github.com/open-ce).

- [Open-CE Automatic Releases](#open-ce-automatic-releases)
  - [Open-CE Release Process](#open-ce-release-process)
  - [Automatic Release Source Code](#automatic-release-source-code)
    - [Python Code](#python-code)
      - [Release Script](#release-script)
      - [Git API and Utility Functions](#git-api-and-utility-functions)
    - [Workflows](#workflows)
      - [PR Workflow](#pr-workflow)
      - [Merge Workflow](#merge-workflow)
      - [Access Token Secret](#access-token-secret)

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
1. If this is not a bug fix, meaning that this is a new release in the main branch,
   then a release branch will be created in the Open-CE
1. A draft release is created in the Open-CE repo that must be manually verified and released.
1. If there are any private feedstocks or env files, those should be tagged and updated correctly.
   - Any env files should have the correct `git_tag_for_env` added to them.
   - Tags should be created in all feedstocks.

## Automatic Release Source Code

### Python Code

#### Release Script

Most of the work for the release happens in the
[create_opence_release.py script](https://github.com/open-ce/open-ce-builder/blob/main/git_tools/create_opence_release.py).

#### Git API and Utility Functions

[git_utils.py](https://github.com/open-ce/open-ce-builder/blob/main/git_tools/git_utils.py)
contains all of the Git API code and most of the git CLI functionality.

### Workflows

The automatic release infrastructure is primarily made up of two workflows.
One that is triggered on PRs and one that is triggered on merges.

#### PR Workflow

The [PR workflow](../.github/workflows/opence-pr.yml) will perform a
"release dry-run" when a PR is made that modifies the the `git_tag_for_env`
field within the [envs/opence-env.yaml](../envs/opence-env.yaml) file.
Meaning that it will do all steps for a release except push anything upstream.

#### Merge Workflow

The [merge workflow](../.github/workflows/opence-merge.yml)
will, if a PR is made that modifies the the `git_tag_for_env`
field within the [envs/opence-env.yaml](../envs/opence-env.yaml)
file, perform a full release.

#### Access Token Secret

The release workflow requires the `API_KEY` secret to be set to a Public Access Token that has access
to the Open-CE repos. The current PAT is set to expire every 3 months, so it needs to be
updated every 3 months.
