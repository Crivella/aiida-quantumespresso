# -*- coding: utf-8 -*-
# pylint: disable=invalid-name,redefined-outer-name
"""Tests for the `BandsxParser`."""
from aiida import orm


def test_bandsx_default(
    aiida_profile, fixture_localhost, generate_parser, generate_calc_job_node, data_regression, num_regression
):
    """Test a normal bands.x output."""
    name = 'default'
    entry_point_calc_job = 'quantumespresso.bandsx'
    entry_point_parser = 'quantumespresso.bandsx'

    node = generate_calc_job_node(entry_point_calc_job, fixture_localhost, name)

    parser = generate_parser(entry_point_parser)

    results, calcfunction = parser.parse_from_node(node, store_provenance=False)

    assert calcfunction.is_finished, calcfunction.exception
    assert calcfunction.is_finished_ok, calcfunction.exit_message
    assert not orm.Log.objects.get_logs_for(node)

    data_regression.check({'output_parameters': results['output_parameters'].get_dict()},
                          basename='test_bandsx_default_data')

    num_regression.check({n:k.reshape(-1) for n,k in results['filband'].get_iterarrays()}, basename='test_bandsx_default_eps')
