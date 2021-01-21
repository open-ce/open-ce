# Open-CE Branching Strategy

This document outlines the overall git branching strategy for the
[Open-CE Organization](https://github.com/open-ce).

- [Open-CE Branching Strategy](#open-ce-branching-strategy)
  - [Feedstock Version Branching](#feedstock-version-branching)
  - [Working Branch](#working-branch)

## Feedstock Version Branching

We want to track upstream version branches for each feedstock. This makes it possible to have environment files select specific versions of feedstocks.

The following branching strategy will be used for feedstocks.

1. All work for the current upstream version will be done in the default branch.

1. When a new version is tagged upstream the following is done:

   - Any Pending PRs should be reviewed and merged.

   - A branch for the previous version should be created at the current head of the default branch.

   - Changes to update the version are pushed to the feedstock default branch.

## Working Branch

We want to ensure that the default branch (`master` or `main` depending on the
repo) always builds in total and take reasonable precautions to keep the
default branch functional. However, this becomes difficult when integrating
new versions of frameworks that may not be compatible or fully integrated yet.

The following branching strategy is to be used under these circumstances.

1. Each repository that needs changes that are potentially breaking gets a
   new branch named after the overall change that is taking place
   (e.g.`pytorch_18_update`). PRs can be made against this branch across all
   repos that need changes.

1. Builds can be performed using the `open-ce` tool by specifying the update
   branch as an input. The `open-ce` tool will automatically use the default
   branch if the specified branch doesn't exist.

    ```shell
    open-ce build env --git_tag_for_env pytorch_18_update envs/opence-env.yaml
    ```

1. Once integration and testing has been finished, the PRs can be created to
   merge all the update branches into default. Merge commits would probably be
   best for these to maintain the separate history.
