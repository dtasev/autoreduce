# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2020 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
""" Utils moudle for sending messages to queues. """
import json

# pylint:disable=cyclic-import
from queue_processors.queue_processor.settings import FACILITY
from utils.clients.queue_client import QueueClient

from model.database import access


class MessagingUtils:
    """ Utils class for sending messages to queues. """
    def send_pending(self, reduction_run, delay=None):
        """ Sends a message to the queue with the details of the job to run. """
        data_dict = self._make_pending_msg(reduction_run)
        self._send_pending_msg(data_dict, delay)

    def send_cancel(self, reduction_run):
        """ Sends a message to the queue telling it to cancel any reruns of the job. """
        data_dict = self._make_pending_msg(reduction_run)
        data_dict["cancel"] = True
        self._send_pending_msg(data_dict)

    @staticmethod
    def _make_pending_msg(reduction_run):
        """ Creates a dict message from the given run, ready to be sent to ReductionPending. """
        # Deferred import to avoid circular dependencies
        # pylint:disable=import-outside-toplevel
        from ..queueproc_utils.reduction_run_utils import ReductionRunUtils

        script, arguments = ReductionRunUtils().get_script_and_arguments(reduction_run)

        # Currently only support single location
        model = access.start_database().data_model
        data_location = model.DataLocation.filter_by(reduction_run_id=reduction_run.id).first()
        if data_location:
            data_path = data_location.file_path
        else:
            raise Exception("No data path found for reduction run")

        data_dict = {
            'run_number': reduction_run.run_number,
            'instrument': reduction_run.instrument.name,
            'rb_number': str(reduction_run.experiment.reference_number),
            'data': data_path,
            'reduction_script': script,
            'reduction_arguments': arguments,
            'run_version': reduction_run.run_version,
            'facility': FACILITY,
            'message': '',
        }

        return data_dict

    @staticmethod
    def _send_pending_msg(data_dict, delay=None):
        """ Sends data_dict to ReductionPending (with the specified delay) """
        # To prevent circular dependencies
        message_client = QueueClient()
        message_client.connect()
        message_client.send('/queue/ReductionPending',
                            json.dumps(data_dict),
                            priority='0',
                            delay=delay)
        message_client.disconnect()
