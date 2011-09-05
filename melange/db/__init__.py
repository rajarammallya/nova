# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2010-2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import optparse

from melange.common import utils
from melange.common import config


db_api = utils.import_object(config.Config.get("db_api_implementation",
                                               "melange.db.sqlalchemy.api"))


def add_options(parser):
    """Adds any configuration options that the db layer might have.

    :param parser: An optparse.OptionParser object
    :retval None

    """
    help_text = ("The following configuration options are specific to the "
                "Melange database.")

    group = optparse.OptionGroup(parser,
                                 "Registry Database Options",
                                 help_text)
    group.add_option('--sql-connection',
                     metavar="CONNECTION",
                     default=None,
                     help="A valid SQLAlchemy connection string for the "
                          "registry database. Default: %default")
    parser.add_option_group(group)
