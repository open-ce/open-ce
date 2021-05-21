# Setting up a new Feedstock

When setting up a new Feedstock in the [Open-CE Organization](https://github.com/open-ce) the following should be done.

- [Setting up a new Feedstock](#setting-up-a-new-feedstock)
  - [Recipe Contents](#recipe-contents)
  - [CI Contents](#ci-contents)
  - [Non-Functional Contents](#non-functional-contents)
    - [`LICENSE` File](#license-file)
    - [`README.md` File](#readmemd-file)
  - [Github Settings](#github-settings)
    - [Naming](#naming)
    - [Squash Merging](#squash-merging)
    - [Branch Protection](#branch-protection)

## Recipe Contents

The feedstock repo should include the files and scripts necessary to build
a conda package. At the very least this should include a `recipe/meta.yaml`.
Examples of this can be found in other
[feedstocks in the Open-CE Organization](https://github.com/open-ce?q=feedstock).

## CI Contents

To enable CI tests, the [`feedstock-pr.yml` file](https://github.com/open-ce/.github/blob/main/workflow-templates/feedstock-pr.yml)
in the [Open-CE/.github repo](https://github.com/open-ce/.github)
should be copied to the new feedstock repo at `.github/workflows/feedstock-pr.yml`

## Non-Functional Contents

All feedstocks should contain a [`LICENSE` file](#license-file) and
a [`README.md` file](#readmemd-file) in the root of the git repo.

### `LICENSE` File

The contents of the `LICENSE` file should be exactly the same as the contents
of every other feedstocks' `LICENSE` file. For example, the
[Spacy `LICENSE` file](https://github.com/open-ce/spacy-feedstock/blob/main/LICENSE)
can be copied directly.

### `README.md` File

The `README.md` files in each feedstock are designed to point people who
land on the feedstock repo back to the main Open-CE repo. The `README.md`
file should be the same, except for the title, which should reflect the name
of the feedstock. The
[Spacy `README.md` file](https://github.com/open-ce/spacy-feedstock/blob/main/README.md)
can be copied, and the title changed.

## Github Settings

### Naming

The name of the repo should be `<package>-feedstock`.

### Squash Merging

Under `Options->Merge button`, only `Allow squash merging` should be checked.

### Branch Protection

The default branch (named `main` in all Open-CE repos) should
have the following protections added:

- `Require pull request reviews before merging`
- `Require status checks to pass before merging`
  - Only `required_tests` should be selected. _Note: this won't be
    avaialble until after the wokflows mentioned in
    [CI Contents](#ci-contents) have already been added to the repo._
- `Include administrators`
