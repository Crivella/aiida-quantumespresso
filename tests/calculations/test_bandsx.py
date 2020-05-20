# -*- coding: utf-8 -*-
"""Tests for the `BandsxCalculation` class."""
from aiida import orm
from aiida.common import datastructures

from aiida_quantumespresso.utils.resources import get_default_options


def test_bandsx_default(
    aiida_profile, fixture_localhost, fixture_sandbox, fixture_code, generate_calc_job, generate_remote_data, tmpdir,
    file_regression
):
    """Test a default `BandsxCalculation`."""
    entry_point_name = 'quantumespresso.bandsx'

    parameters = {
        'BANDS': {
            'parity': True,
            'lsigma': False,
            'lsym': False,
        }
    }

    parent = generate_remote_data(
        fixture_localhost,
        str(tmpdir),
        'quantumespresso.pw',
    )

    inputs = {
        'code': fixture_code(entry_point_name),
        'parameters': orm.Dict(dict=parameters),
        'parent_folder': parent,
        'metadata': {
            'options': get_default_options()
        }
    }

    calc_info = generate_calc_job(fixture_sandbox, entry_point_name, inputs)

    retrieve_list = ['aiida.out', 'filband', 'm_elems', 'filband.gnu', 'filband.rap', 'filband.par', 'filband.1', 'filband.2', 'filband.3']

    assert isinstance(calc_info, datastructures.CalcInfo)
    assert sorted(calc_info.retrieve_list) == sorted(retrieve_list)

    with fixture_sandbox.open('aiida.in') as handle:
        input_written = handle.read()

    # Checks on the files written to the sandbox folder as raw input
    assert sorted(fixture_sandbox.get_content_list()) == sorted(['aiida.in'])
    file_regression.check(input_written, encoding='utf-8', extension='.in')
