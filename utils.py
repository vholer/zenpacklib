##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

import functools
import importlib
from Products.ZenUtils.guid.interfaces import IGlobalIdentifier
from Products.ZenUtils.Utils import monkeypatch:$

def guid(obj):
    '''Return GUID for obj.'''
    return IGlobalIdentifier(obj).getGUID()

def add_contained(obj, relname, target):
    '''
    Add and return obj to containing relname on target.
    '''
    rel = getattr(obj, relname)
    # import pdb; pdb.set_trace()
    rel._setObject(target.id, target)
    return rel._getOb(target.id)

def add_noncontained(obj, relname, target):
    '''
    Add obj to non-containing relname on target.
    '''
    rel = getattr(obj, relname)
    rel.addRelation(target)

def require_zenpack(zenpack_name, default=None):
    '''
    Decorator with mandatory zenpack_name argument.

    If zenpack_name can't be imported, the decorated function or method
    will return default. Otherwise it will execute and return as
    written.

    Usage looks like the following:

        @require_zenpack('ZenPacks.zenoss.Impact')
        @require_zenpack('ZenPacks.zenoss.vCloud')
        def dothatthingyoudo(args):
            return "OK"

        @require_zenpack('ZenPacks.zenoss.Impact', [])
        def returnalistofthings(args):
            return [1, 2, 3]
    '''
    def wrap(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                importlib.import_module(zenpack_name)
            except ImportError:
                return

            return f(*args, **kwargs)

        return wrapper

    return wrap

def impacts_for(thing):
    '''
    Return a two element tuple.

    First element is a list of object ids impacted by thing. Second element is
    a list of object ids impacting thing.
    '''
    from ZenPacks.zenoss.Impact.impactd.interfaces \
        import IRelationshipDataProvider

    impacted_by = []
    impacting = []

    guid_manager = IGUIDManager(thing.getDmd())
    for subscriber in subscribers([thing], IRelationshipDataProvider):
        for edge in subscriber.getEdges():
            if edge.source == guid(thing):
                impacted_by.append(guid_manager.getObject(edge.impacted).id)
            elif edge.impacted == guid(thing):
                impacting.append(guid_manager.getObject(edge.source).id)

    return (impacted_by, impacting)


def triggers_for(thing):
    '''
    Return a dictionary of triggers for thing.

    Returned dictionary keys will be triggerId of a Trigger instance and
    values will be the corresponding Trigger instance.
    '''
    from ZenPacks.zenoss.Impact.impactd.interfaces import INodeTriggers

    triggers = {}

    for sub in subscribers((thing,), INodeTriggers):
        for trigger in sub.get_triggers():
            triggers[trigger.triggerId] = trigger

    return triggers
