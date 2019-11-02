"""PyLint Reporter that emits TeamCity service messages.
This allows PyLint messages to be processed by TeamCity and displayed on the Code Inspection tab
"""

import os
from pylint import reporters
from pylint.__pkginfo__ import numversion as pylint_numversion
from teamcity import messages


# Maps PyLint categories to TeamCity Inspection SEVERITY classes
TC_SEVERITY = {
    'info': 'INFO',
    'convention': 'INFO',
    'refactor': 'WEAK WARNING',
    'warning': 'WARNING',
    'error': 'ERROR',
    'fatal': 'FATAL'
}


def get_message_description(linter, msgid):
    if pylint_numversion < (2, 0):
        return linter.msgs_store.check_message_id(msgid).descr
    elif pylint_numversion < (2, 3):
        return linter.msgs_store.get_message_definition(msgid).descr
    else:
        # >= 2.3
        return " ".join(definition.description for definition in linter.msgs_store.get_message_definitions(msgid))


class TeamCityReporter(reporters.BaseReporter):
    """PyLint Reporter that emits TeamCity service messages."""

    def __init__(self):
        super(TeamCityReporter, self).__init__()
        self.tc = messages.TeamcityServiceMessages()
        self.msg_types = set()

    def report_message_type(self, msg):
        """Issues an `inspectionType` service message to define generic properties of a given PyLint message type.
        :param utils.Message msg: a PyLint message
        """
        desc = get_message_description(self.linter, msg.msg_id)
        self.tc.message('inspectionType', id=msg.msg_id, name=msg.symbol, description=desc if desc else msg.symbol, category=msg.category)

    def handle_message(self, msg):
        """Issues an `inspection` service message based on a PyLint message.
        Registers each message type upon first encounter.

        :param utils.Message msg: a PyLint message
        """
        if msg.msg_id not in self.msg_types:
            self.report_message_type(msg)
            self.msg_types.add(msg.msg_id)

        self.tc.message('inspection', typeId=msg.msg_id, message=msg.msg,
                        file=os.path.relpath(msg.abspath).replace('\\', '/'),
                        line=str(msg.line),
                        SEVERITY=TC_SEVERITY.get(msg.category))

    def display_reports(self, layout):
        """Issues the final PyLint score as a TeamCity build statistic value"""
        try:
            score = self.linter.stats['global_note']
        except (AttributeError, KeyError):
            pass
        else:
            self.tc.message('buildStatisticValue', key='PyLintScore', value=str(score))
