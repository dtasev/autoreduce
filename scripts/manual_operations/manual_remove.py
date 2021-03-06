# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Functionality to remove a reduction run from the database
"""
from __future__ import print_function

import sys

import fire

from scripts.manual_operations.util import get_run_range
from utils.clients.django_database_client import DatabaseClient
from model.database import access as db


class ManualRemove:
    """
    Handles removing a run from the database
    """

    def __init__(self, instrument):
        """
        :param instrument: (str) The name of the instrument associated with runs
        """
        self.database = DatabaseClient()
        self.database.connect()
        self.to_delete = {}
        self.instrument = instrument

    def find_runs_in_database(self, run_number):
        """
        Find all run versions in the database that relate to a given instrument and run number
        :param run_number: (int) The run to search for in the database
        :return: The result of the query
        """
        instrument_record = db.get_instrument(self.instrument)
        result = self.database.data_model.ReductionRun.objects \
            .filter(instrument=instrument_record.id) \
            .filter(run_number=run_number) \
            .order_by('-created')
        self.to_delete[run_number] = result
        return result

    def process_results(self):
        """
        Process all the results what to do with the run based on the result of database query
        """
        copy_to_delete = self.to_delete.copy()
        for key, value in copy_to_delete.items():
            if not value:
                self.run_not_found(run_number=key)
            if len(value) == 1:
                continue
            if len(value) > 1:
                self.multiple_versions_found(run_number=key)

    def run_not_found(self, run_number):
        """
        Inform user and remove key from dictionary
        :param run_number: (int) The run to remove from the dictionary
        """
        print('No runs found associated with {} for instrument {}'.format(run_number,
                                                                          self.instrument))
        del self.to_delete[run_number]

    def multiple_versions_found(self, run_number):
        """
        Ask the user which versions they want to remove
        Update the self.to_delete dictionary by removing unwanted versions
        :param run_number: (int) The run number with multiple versions
        """
        # Display run_number - title - version for all matching runs
        print("Discovered multiple reduction versions for {}{}:".format(self. instrument,
                                                                        run_number))
        for run in self.to_delete[run_number]:
            print("\tv{} - {}".format(run.run_version, run.run_name))

        # Get user input for which versions they wish to delete
        user_input = input("Which runs would you like to delete (e.g. 1,2,3): ")
        input_valid, user_input = self.validate_csv_input(user_input)
        while input_valid is False:
            user_input = input('Input of \'{}\' was invalid. '
                               'Please provide a comma separated list of values:')
            input_valid, user_input = self.validate_csv_input(user_input)

        # Remove runs that the user does NOT want to delete from the delete list
        for reduction_job in self.to_delete[run_number]:
            if not int(reduction_job.run_version) in user_input:
                self.to_delete[run_number].remove(reduction_job)

    def delete_records(self):
        """
        Delete all records from the database that match those found in self.to_delete
        """
        # Make a copy to ensure dict being iterated stays same size through processing
        to_delete_copy = self.to_delete.copy()
        for run_number, job_list in to_delete_copy.items():
            for version in job_list:
                # Delete the specified version
                print('{}{}:'.format(self.instrument, run_number))
                self.delete_reduction_location(version.id)
                self.delete_data_location(version.id)
                self.delete_variables(version.id)
                self.delete_reduction_run(version.id)

            # Remove deleted run from dictionary
            del self.to_delete[run_number]

    def delete_reduction_location(self, reduction_run_id):
        """
        Delete a ReductionLocation record from the database
        :param reduction_run_id: (int) The id of the associated reduction job
        """
        self.database.data_model.ReductionLocation.objects \
            .filter(reduction_run_id=reduction_run_id) \
            .delete()

    def delete_data_location(self, reduction_run_id):
        """
        Delete a DataLocation record from the database
        :param reduction_run_id: (int) The id of the associated reduction job
        """
        self.database.data_model.DataLocation.objects \
            .filter(reduction_run_id=reduction_run_id) \
            .delete()

    def delete_variables(self, reduction_run_id):
        """
        Removes all the RunVariable records associated with a given ReductionRun from the database
        :param reduction_run_id: (int) The id of the associated reduction job
        """
        run_variables = self.find_variables_of_reduction(reduction_run_id)
        for record in run_variables:
            self.database.variable_model.RunVariable.objects \
                .filter(variable_ptr_id=record.variable_ptr_id) \
                .delete()

    def find_variables_of_reduction(self, reduction_run_id):
        """
        Find all the RunVariable records in the database associated with a reduction job
        :param reduction_run_id: (int) The id of the reduction job to filter by
        :return: (QuerySet) of the associated RunVariables
        """
        return self.database.variable_model.RunVariable.objects \
            .filter(reduction_run_id=reduction_run_id)

    def delete_reduction_run(self, reduction_run_id):
        """
        Delete a ReductionRun record from the database
        :param reduction_run_id: (int) The id of the associated reduction job
        """
        self.database.data_model.ReductionRun.objects \
            .filter(id=reduction_run_id) \
            .delete()

    @staticmethod
    def validate_csv_input(user_input):
        """
        checks if a comma separated list was provided
        :return: (tuple) = (bool - is valid? , list - csv as list (empty list if invalid))
        """
        processed_input = []
        if ',' in user_input:
            versions_to_delete = user_input.split(',')
            for number in versions_to_delete:
                try:
                    number = int(number)
                    processed_input.append(number)
                except ValueError:
                    return False, []
        else:
            try:
                user_input = int(user_input)
                processed_input.append(user_input)
            except ValueError:
                return False, []
        return True, processed_input


def remove(instrument, run_number):
    """
    Run the remove script
    :param instrument:
    :param run_number:
    """
    manual_remove = ManualRemove(instrument)
    manual_remove.find_runs_in_database(run_number)
    manual_remove.process_results()
    manual_remove.delete_records()


def user_input_check(instrument, run_numbers):
    """
    User prompt for boolean value to to assert if user really wants to remove N runs
    :param instrument (str) Instrument name related to runs user intends to remove
    :param run_numbers (range object) range of instruments submitted by user
    :return (bool) True or False to confirm removal of N runs or exit script
    """
    valid = {"Y": True, "N": False}

    print(f"You are about to remove more than 10 runs from {instrument} \n"
          f"Are you sure you want to remove run numbers: {run_numbers[0]}-{run_numbers[-1]}?")
    user_input = input("Please enter Y or N: ").upper()

    try:
        return valid[user_input]
    except KeyError:
        print("Invalid input, please enter either 'Y' or 'N' to continue to exit script")
    return user_input


def main(instrument: str, first_run: int, last_run: int = None):
    """
    Parse user input and run the script to remove runs for a given instrument
    :param instrument: (str) Instrument to run on
    :param first_run: (int) First run to be removed
    :param last_run: (int) Optional last run to be removed
    """
    run_numbers = get_run_range(first_run, last_run=last_run)

    instrument = instrument.upper()

    if len(run_numbers) >= 10:
        user_input = user_input_check(instrument, run_numbers)
        if not user_input:
            sys.exit()

    for run in run_numbers:
        remove(instrument, run)


if __name__ == "__main__":  # pragma: no cover
    fire.Fire(main)
