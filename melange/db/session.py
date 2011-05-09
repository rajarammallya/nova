_ENGINE=None
_MAKER=None

import logging

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import exc
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import sessionmaker

from melange.common import config

def configure_db(options):
    global _ENGINE
    if not _ENGINE:
        debug = config.get_option(options,
                                  'debug', type='bool', default=False)
        verbose = config.get_option(options,
                                    'verbose', type='bool', default=False)
        timeout = config.get_option(options,
                                    'sql_idle_timeout', type='int', default=3600)
        _ENGINE = create_engine(options['sql_connection'],
                                pool_recycle=timeout)
        logger = logging.getLogger('sqlalchemy.engine')

        if debug:
            logger.setLevel(logging.DEBUG)
        elif verbose:
            logger.setLevel(logging.INFO)

def get_session(autocommit=True, expire_on_commit=False):
        """Helper method to grab session"""
        global _MAKER, _ENGINE            
        if not _MAKER:
            assert _ENGINE
            _MAKER = sessionmaker(bind=_ENGINE,
                                  autocommit=autocommit,
                                  expire_on_commit=expire_on_commit)
        return _MAKER()
