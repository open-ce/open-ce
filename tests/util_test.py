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

import sys
import os
import pathlib
sys.path.append(os.path.join(pathlib.Path(__file__).parent.absolute(), '..', 'builder'))

import pytest
import utils

def test_parse_arg_list_list_input():
    '''
    Parse arg list should return the input argument if it's already a list.
    '''
    list_input = ["a", "b", "c"]
    assert list_input == utils.parse_arg_list(list_input)

def test_parse_arg_list_small_string_input():
    '''
    Tests that parse_arg_list works for a simple case.
    '''
    string_input = "a,b,c"
    list_output = ["a", "b", "c"]
    assert list_output == utils.parse_arg_list(string_input)

def test_parse_arg_list_large_string_input():
    '''
    Test parse_arg_list with a more complicated input, including spaces.
    '''
    string_input = "this,is a, big  , test  ,"
    list_output = ["this", "is a", " big  ", " test  ", ""]
    assert list_output == utils.parse_arg_list(string_input)
