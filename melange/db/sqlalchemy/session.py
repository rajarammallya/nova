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

_ENGINE = None
_MAKER = None
_MODELS = None

import logging
import contextlib

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

from melange.common import config
from melange.db.sqlalchemy import mappers


def configure_db(options):
    configure_sqlalchemy_log(options)
    global _ENGINE, _MODELS
    if not _ENGINE:
        _ENGINE = _create_engine(options)

        _MODELS = _models(_ENGINE, options)


def _models(engine, options):

    mappers.map(_ENGINE, options['models'])

    models = options['models']
    models['ip_nat_relation'] = mappers.IpNat

    return models


def configure_sqlalchemy_log(options):
    debug = config.get_option(options,
                              'debug', type='bool', default=False)
    verbose = config.get_option(options,
                                'verbose', type='bool', default=False)
    logger = logging.getLogger('sqlalchemy.engine')
    if debug:
        logger.setLevel(logging.DEBUG)
    elif verbose:
        logger.setLevel(logging.INFO)


def _create_engine(options):
    timeout = config.get_option(options,
                                'sql_idle_timeout', type='int', default=3600)
    return create_engine(options['sql_connection'],
                                pool_recycle=timeout)


def models():
    global _MODELS
    assert _MODELS
    return _MODELS


def get_session(autocommit=True, expire_on_commit=False):
    """Helper method to grab session"""
    global _MAKER, _ENGINE
    if not _MAKER:
        assert _ENGINE
        _MAKER = sessionmaker(bind=_ENGINE,
                              autocommit=autocommit,
                              expire_on_commit=expire_on_commit)
    return _MAKER()


def raw_query(model, autocommit=True, expire_on_commit=False):
    return get_session(autocommit, expire_on_commit).query(model)


def clean_db():
    global _ENGINE
    meta = MetaData()
    meta.reflect(bind=_ENGINE)
    with contextlib.closing(_ENGINE.connect()) as con:
        trans = con.begin()
        for table in reversed(meta.sorted_tables):
            if table.name != "migrate_version":
                con.execute(table.delete())
        trans.commit()


def drop_db(options):
    meta = MetaData()
    engine = _create_engine(options)
    meta.bind = engine
    meta.reflect()
    meta.drop_all()
