# Open-CE Branching Strategy

This document outlines the overall git branching strategy for the
[Open-CE Organization](https://github.com/open-ce).

- [Open-CE Branching Strategy](#open-ce-branching-strategy)
  - [Feedstock Version Branching](#feedstock-version-branching)
  - [Working Branch](#working-branch)

## Feedstock Version Branching

TBD

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
