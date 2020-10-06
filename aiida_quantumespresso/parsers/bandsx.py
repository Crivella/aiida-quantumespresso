# -*- coding: utf-8 -*-
"""`Parser` implementation for the `BandsxCalculation` calculation job class."""
import numpy as np
from io import StringIO
from aiida import orm
from aiida.common import exceptions

from aiida_quantumespresso.calculations.bandsx import BandsxCalculation
from .base import Parser


class BandsxParser(Parser):
    """`Parser` implementation for the `BandsxCalculation` calculation job class."""

    def parse(self, **kwargs):
        """Parse the retrieved files of a completed `BandsxCalculation` into output nodes.

        Two nodes that are expected are the default 'retrieved' `FolderData` node which will store the retrieved files
        permanently in the repository. The second required node is a filepath under the key `retrieved_temporary_files`
        which should contain the temporary retrieved files.
        """
        self.exit_code_stdout = None
        self.exit_code_filband_files = None

        try:
            self.retrieved
        except exceptions.NotExistent:
            return self.exit(self.exit_codes.ERROR_NO_RETRIEVED_FOLDER)

        # Parse the pw2gw stout file
        data, logs_stdout = self.parse_stdout()

        self.emit_logs(logs_stdout)

        if self.exit_code_stdout:
            return self.exit(self.exit_code_stdout)

        self.out('output_parameters', orm.Dict(dict=data))

        # Parse the bandsx outputfiles
        filband = self.parse_filband_files()

        if self.exit_code_filband_files:
            return self.exit(self.exit_code_filband_files)

        self.out('filband', filband)

    def parse_filband_files(self):
        """Parse the eps*.dat files produced by pw2gw.x and store them in the `eps` node."""
        from aiida_quantumespresso.parsers.parse_raw.bandsx import parse_filband_file

        retrieved = self.retrieved
        retrieved_names = retrieved.list_object_names()

        # files = BandsxCalculation._internal_retrieve_list
        if not BandsxCalculation._FILBAND in retrieved_names:
            self.exit_code_filband_files = self.exit_codes.ERROR_OUTPUT_FILES
            return

        filband = orm.ArrayData()

        content = self.retrieved.get_object_content(BandsxCalculation._FILBAND)
        parsed_data, logs = parse_filband_file(content)
        self.emit_logs(logs)

        filband.set_array('kpts', parsed_data['kpts'])
        filband.set_array('egv', parsed_data['data'])

        if BandsxCalculation._RAP in retrieved_names:
            content = self.retrieved.get_object_content(BandsxCalculation._RAP)
            parsed_data, logs = parse_filband_file(content)
            self.emit_logs(logs)
            filband.set_array('rap', parsed_data['data'])

        if BandsxCalculation._PAR in retrieved_names:
            content = self.retrieved.get_object_content(BandsxCalculation._PAR)
            parsed_data, logs = parse_filband_file(content)
            self.emit_logs(logs)
            filband.set_array('par', parsed_data['data'])

        if BandsxCalculation._SPIN1 in retrieved_names:
            content = self.retrieved.get_object_content(BandsxCalculation._SPIN1)
            parsed_data, logs = parse_filband_file(content)
            self.emit_logs(logs)
            filband.set_array('lsigma1', parsed_data['data'])

            content = self.retrieved.get_object_content(BandsxCalculation._SPIN2)
            parsed_data, logs = parse_filband_file(content)
            self.emit_logs(logs)
            filband.set_array('lsigma2', parsed_data['data'])

            content = self.retrieved.get_object_content(BandsxCalculation._SPIN3)
            parsed_data, logs = parse_filband_file(content)
            self.emit_logs(logs)
            filband.set_array('lsigma3', parsed_data['data'])

        return filband

    def parse_stdout(self):
        """Parse the stdout file of bands.x to build the `output_parameters` node."""
        from aiida_quantumespresso.utils.mapping import get_logging_container
        from aiida_quantumespresso.parsers.parse_raw.bandsx import parse_stdout

        logs = get_logging_container()
        parsed_data = {}

        filename_stdout = self.node.get_attribute('output_filename')

        if filename_stdout not in self.retrieved.list_object_names():
            self.exit_code_stdout = self.exit_codes.ERROR_OUTPUT_STDOUT_MISSING
            return parsed_data, logs

        try:
            stdout = self.retrieved.get_object_content(filename_stdout)
        except IOError:
            self.exit_code_stdout = self.exit_codes.ERROR_OUTPUT_STDOUT_READ
            return parsed_data, logs

        try:
            parsed_data, logs = parse_stdout(stdout)
        except Exception:
            import traceback
            traceback.print_exc()
            self.exit_code_stdout = self.exit_codes.ERROR_UNEXPECTED_PARSER_EXCEPTION

        # If the stdout was incomplete, most likely the job was interrupted before it could cleanly finish, so the
        # output files are most likely corrupt and cannot be restarted from
        if 'ERROR_OUTPUT_STDOUT_INCOMPLETE' in logs['error']:
            self.exit_code_stdout = self.exit_codes.ERROR_OUTPUT_STDOUT_INCOMPLETE

        return parsed_data, logs
