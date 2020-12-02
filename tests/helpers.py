# *****************************************************************
#
# Licensed Materials - Property of IBM
#
# (C) Copyright IBM Corp. 2020. All Rights Reserved.
#
# US Government Users Restricted Rights - Use, duplication or
# disclosure restricted by GSA ADP Schedule Contract with IBM Corp.
#
# *****************************************************************

import os

class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

def validate_cli(cli_string, expect=None, reject=None, ignore=None, possible_expect=None, retval=0):
    """
    Used to mock os.system with the assumption that it is making a call to 'conda-build'.

    Args:
        cli_string: The placeholder argument for the system command.
        expect: A list of strings that must occur in the 'cli_string' arg.
        reject: A list of strings that cannot occur in the 'cli_string' arg.
        ignore: Don't validate the CLI_STRING if one of these strings is contained in it.
        possible_expect: A list of possible strings that the CLI may contain. CLI should contain
                        at least one of these.
        retval: The mocked value to return from 'os.system'.
    Returns:
        retval
    """
    if not expect: expect = []
    if not reject: reject = []
    if not ignore: ignore = []
    if not possible_expect: possible_expect = []

    if not any ({term in cli_string for term in ignore}):
        for term in expect:
            assert term in cli_string
        for term in reject:
            assert term not in cli_string
        if len(expect) == 0:
            assert any ({term in cli_string for term in possible_expect})
        return retval
    return 0

def validate_conda_build_args(recipe, expect_recipe=None, expect_config=None, expect_variants=None, reject_recipe=None, **kwargs):
    """
    Used to mock `conda_build.api.build`

    Args:
        recipe: The placeholder argument for the conda_build.api.build 'recipe' arg.
        expect_recipe: A string that must occur in the 'recipe' arg.
        expect_config: A dict for the keys and values that must occur in the 'config' arg.
        expect_variants: A dict for the keys and values that must occur in the 'variants' arg.
        reject_recipe: A string that cannot occur in the 'recipe` arg.
    """
    if not expect_recipe: expect_recipe = []
    if not expect_config: expect_config = []
    if not expect_variants: expect_variants = []
    if not reject_recipe: reject_recipe = []

    if expect_recipe:
        assert recipe in expect_recipe
    if reject_recipe:
        assert recipe not in reject_recipe

    if expect_config:
        config = kwargs['config']
        for term, value in expect_config.items():
            assert hasattr(config, term)
            assert getattr(config, term) == value
    if expect_variants:
        variants = kwargs['variants']
        for term, value in expect_variants.items():
            assert term in variants
            assert variants.get(term) == value

class DirTracker(object):
    def __init__(self, starting_dir=os.getcwd()):
        self.current_dir = starting_dir
        self.chdir_count = 0

    def validate_chdir(self, arg1, expected_dirs=None):
        """
        Used to mock os.chdir. Each time a directory is changed, the global counter ch_dir is incremented,
        and each change is validated against the expected_dirs list.
        The current directory is tracked in `current_dir` and used by `mocked_getcwd`.

        Args:
            arg1: The placeholder argumentfor the chdir command.
            expected_dirs: The list of directories that are expected to be chdired during execution..
        Returns:
            0
        """
        if expected_dirs and self.chdir_count < len(expected_dirs):
            assert arg1 == expected_dirs[self.chdir_count]
        self.current_dir = arg1
        self.chdir_count+=1
        return 0

    def mocked_getcwd(self):
        return self.current_dir

def make_render_result(package_name, build_reqs=None, run_reqs=None, host_reqs=None, test_reqs=None,
                          string=None):
    '''
    Creates a YAML string that is a mocked result of `conda_build.api.render`.
    '''
    if not build_reqs: build_reqs = []
    if not run_reqs: run_reqs = []
    if not host_reqs: host_reqs = []
    if not test_reqs: test_reqs = []
    if not string: string = ''

    retval = [(Namespace(meta={
                            'package': {'name': package_name, 'version': '1.2.3'},
                            'source': {'git_url': 'https://github.com/'+package_name+'.git', 'git_rev': 'v0.19.5', 'patches': []},
                            'build': {'number': '1', 'string': 'py37_1'},
                            'requirements': {'build': build_reqs, 'host': host_reqs, 'run': run_reqs + ["upstreamdep1   2.3","upstreamdep2   2"], 'run_constrained': []},
                            'test': {'requires': test_reqs},
                            'about': {'home': 'https://github.com/'+package_name+'.git', 'license_file': 'LICENSE', 'summary': package_name},
                            'extra': {'final': True}}),
                      True,
                      None)]
    return retval

def mock_renderer(path, package_deps):
    '''
    Used to mock the `conda_build.api.render` function by extracting the package name from `path`
    and using that to get the dependencies from `package_deps`.
    '''
    package = os.path.basename(path)[:-10]
    return make_render_result(package, package_deps[package])
