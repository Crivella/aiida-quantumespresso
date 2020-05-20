# -*- coding: utf-8 -*-
"""A collection of function that are used to parse the output of Quantum Espresso bands.x.

The function that needs to be called from outside is parse_raw_output(). The functions mostly work without aiida
specific functionalities. The parsing will try to convert whatever it can in some dictionary, which by operative
decision doesn't have much structure encoded, [the values are simple ]
"""
import re
import numpy as np

from aiida_quantumespresso.parsers import QEOutputParsingError
from aiida_quantumespresso.parsers.parse_raw import convert_qe_time_to_sec
from aiida_quantumespresso.utils.mapping import get_logging_container


def parse_stdout(stdout):
    """Parses the stdout content of a Quantum ESPRESSO `bands.x` calculation.

    :param stdout: the stdout content as a string
    :returns: tuple of two dictionaries, with the parsed data and log messages, respectively
    """
    # Separate the input string into separate lines
    data_lines = stdout.split('\n')

    logs = get_logging_container()

    parsed_data = {}

    for line in data_lines:
        if 'JOB DONE' in line:
            break
    else:
        logs.error.append('ERROR_OUTPUT_STDOUT_INCOMPLETE')

    for count, line in enumerate(data_lines):
        if 'BANDS' in line and 'WALL' in line:
            try:
                time = line.split('CPU')[1].split('WALL')[0]
                parsed_data['wall_time'] = time
            except Exception:
                logs.warning.append('Error while parsing wall time.')
            try:
                parsed_data['wall_time_seconds'] = convert_qe_time_to_sec(time)
            except ValueError:
                raise QEOutputParsingError('Unable to convert wall_time in seconds.')

    return parsed_data, logs

def parse_filband_file(content):
    data_lines = content.split('\n')

    logs = get_logging_container()

    parsed_data = {}


    res = re.finditer(r'nbnd(_\w*)? *= *(?P<nbnd>\d*) *, *nks(_\w*)? *= *(?P<nks>\d*)', data_lines[0])
    dct = list(res)[0].groupdict()
    nbnd = int(dct['nbnd'])
    nks  = int(dct['nks'])

    app1 = ' '.join(data_lines[1:])
    app1 = app1.replace('\n', ' ')
    app1 = app1.replace('T', ' ').replace('F', ' ')
    data = list(map(lambda x: float(x), filter(None, app1.split(' '))))

    a = nbnd + 3
    kpts = []
    res = []
    for i in range(nks):
        # print(i)
        new_kpt = []
        for j in range(3):
            new_kpt.append(data[a*i + j])
        kpts.append(new_kpt)

        new_res = []
        for j in range(nbnd):
            new_res.append(data[a*i + j + 3])
        res.append(new_res)

    parsed_data['kpts'] = np.array(kpts)
    parsed_data['data'] = np.array(res)

    return parsed_data, logs
