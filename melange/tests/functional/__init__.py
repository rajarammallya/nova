# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
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

import os
import shutil
import socket
import subprocess

import melange
from melange.common import config
from melange.db import db_api
from melange.tests.functional import server


_PORT = None


def setup():
    print "Restarting melange server..."
    shutil.copyfile(melange.melange_etc_path("melange.conf.sample"),
                    os.path.expanduser("~/melange.conf"))
    srv = server.Server("melange",
                         melange.melange_bin_path('melange'))
    _db_sync()
    srv.restart(port=setup_unused_port())
    _configure_db()


def _configure_db():
    conf_file, conf = config.load_paste_config("melange", {}, None)
    db_api.configure_db(conf)


def _db_sync():
    conf_file, conf = config.load_paste_config("melange", {}, None)
    db_api.db_sync(conf)


def teardown():
    print "Stopping melange server..."
    server.Server("melange", melange.melange_bin_path('melange')).stop()


def execute(cmd, raise_error=True):
    """Executes a command in a subprocess.
    Returns a tuple of (exitcode, out, err), where out is the string output
    from stdout and err is the string output from stderr when
    executing the command.

    :param cmd: Command string to execute
    :param raise_error: If returncode is not 0 (success), then
                        raise a RuntimeError? Default: True)

    """

    env = os.environ.copy()

    # Make sure that we use the programs in the
    # current source directory's bin/ directory.
    env['PATH'] = melange.melange_bin_path() + ':' + env['PATH']
    process = subprocess.Popen(cmd,
                               shell=True,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               env=env)
    result = process.communicate()
    (out, err) = result
    exitcode = process.returncode
    if process.returncode != 0 and raise_error:
        msg = "Command %(cmd)s did not succeed. Returned an exit "\
              "code of %(exitcode)d."\
              "\n\nSTDOUT: %(out)s"\
              "\n\nSTDERR: %(err)s" % locals()
        raise RuntimeError(msg)
    return exitcode, out, err


def get_unused_port():
    """Returns an unused port on localhost."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('localhost', 0))
    addr, port = s.getsockname()
    s.close()
    return port


def setup_unused_port():
    global _PORT
    _PORT = get_unused_port()
    return _PORT


def get_api_port():
    return _PORT
