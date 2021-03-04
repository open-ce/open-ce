# Builder Tests

## Required Conda Packages

The following packages are required to run the tests:

* pytest
* pytest-cov
* pytest-mock

```shell
$ conda install pytest pytest-cov pytest-mock
...
```

## Running Tests

`pytest.ini` contains configuration information.

To execute the tests use the following command:

```shell
$ pytest tests/
================================================================================ test session starts =================================================================================
platform linux -- Python 3.7.7, pytest-6.0.1, py-1.9.0, pluggy-0.13.1
rootdir: ~/git/open-ce
plugins: cov-2.10.0, mock-3.2.0
collected 10 items

tests/build_feedstock_test.py .......                                                                                                                                          [ 70%]
tests/util_test.py ...                                                                                                                                                         [100%]

----------- coverage: platform linux, python 3.7.7-final-0 -----------
Name                         Stmts   Miss  Cover   Missing
----------------------------------------------------------
open_ce/__init__.py              0      0   100%
open_ce/build_env.py           163    163     0%   2-332
open_ce/build_feedstock.py      83      6    93%   173-178, 193
open_ce/utils.py                  4      0   100%
----------------------------------------------------------
TOTAL                          250    169    32%

================================================================================= 10 passed in 0.59s =================================================================================
```
