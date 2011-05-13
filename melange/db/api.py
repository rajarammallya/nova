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

from melange.db import session

def find_all_by(cls,**kwargs):
    return base_query(cls).filter_by(**kwargs)

def find_by(cls, **kwargs):
    return find_all_by(cls,**kwargs).first()

def find(cls, id):
    return base_query(cls).get(id)

def save(model):
    db_session = session.get_session()
    model = db_session.merge(model)
    db_session.flush()
    return model

def delete(model):
    db_session = session.get_session()
    model = db_session.merge(model)
    db_session.delete(model)
    db_session.flush()

def base_query(cls):
    return  session.get_session().query(cls)
    
