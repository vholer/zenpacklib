#!/usr/bin/env python
from pyparsing import (Suppress,
                       Word,
                       alphanums,
                       OneOrMore,
                       delimitedList,
                       SkipTo,
                       Optional,
                       Group,
                       dictOf)
delimitedList, SkipTo, Optional
import glob
import ast
import os
import fnmatch
from pprint import pprint
from ast import ClassDef, Assign, Name, Str, BinOp, Tuple, Dict, Call


def find_files(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for basename in files:
            if fnmatch.fnmatch(basename, pattern):
                filename = os.path.join(root, basename)
                yield filename


class RelationFactory(object):
    def __init__(self, lclass, lrelname, lreltype, rreltype, rclass, rrelname):
        self.lclass = lclass
        self.lrelname = lrelname
        self.lreltype = lreltype
        self.rreltype = rreltype
        self.rclass = rclass
        self.rrelname = rrelname

    def __repr__(self):
        return '(\'%s\', %s(%s, \'%s\', \'%s\',))' % (self.lrelname,
                                                      self.lreltype,
                                                      self.rreltype,
                                                      self.rclass,
                                                      self.rrelname)

    def reverse(self):
        return RelationFactory(self.rclass, self.rrelname, self.rreltype,
                               self.lreltype, self.lclass, self.rrelname)

    def sort(self):
        'method used to sort the yuml into containing and non-containing'
        if 'Cont' in self.rreltype or 'Cont' in self.lreltype:
            prefix = '0'
        else:
            prefix = '1'

        return prefix + self.yuml()

    def yuml(self):
        def card_conv(data):
            if data == 'ToManyCont':
                return '++'
            elif data == 'ToMany':
                return '*'
            else:
                return ''

        lc = self.lclass
        lreln = self.lrelname
        lcard = card_conv(self.lreltype)
        rc = self.rclass
        rreln = self.rrelname
        rcard = card_conv(self.rreltype)

        # reverse this if its a one->many .. so its consistently displayed
        if lcard == '' and rcard in ['*', '++']:
            return self.reverse().yuml()
        return "[{0}]{1}{2} -.- {3}{4}[{5}]".format(lc, lcard, lreln, rreln, rcard, rc)


def print_relationships_yuml(relationships):
    output = "RELATIONSHIPS_YUML = \"\"\"\n"
    for x in sorted(relationships, key=lambda x: x.sort()):
        output = output + '%s\n' % x.yuml()
    output = output + '"""'
    return output

registerName = Suppress('ZC.registerName(\'')
sQuote = Suppress('\'').setName('\'')
comma = Suppress(',').setName(',')
underscoreTParen = Suppress('_t(').setName('_t(')
rParen = Suppress(')').setName(')')
rCurly = Suppress('}').setName('}')
lCurly = Suppress('{').setName('{')
lBracket = Suppress('[').setName('[')
rBracket = Suppress(']').setName(']')
colon = Suppress(':').setName(':')
semicolon = Suppress(';').setName(';')
noSpaceWord = Word(alphanums+'_').setName('noSpaceWord')
Words = OneOrMore(Word(alphanums+'_.\/')).setParseAction( lambda tokens : " ".join(tokens)).setName('Words')
underscoreTWords = (underscoreTParen + sQuote + Words + sQuote + rParen).setName('underscoreTWords')
quotedWords = (sQuote + Words + sQuote).setName('quotedWords')
klass_labels = Suppress('ZC.registerName(\'') + noSpaceWord + dictOf(sQuote,\
        comma + delimitedList(underscoreTWords))

start = Suppress(SkipTo('||{}', include=True)) + comma + lCurly
end = rCurly + rParen + semicolon
propAttributes = dictOf(Words + colon, (Words ^ quotedWords ^ underscoreTWords) + Optional(comma))
prop = lCurly + Group(propAttributes) + rCurly
props = delimitedList(prop) + Optional(comma)
listObj = (lBracket + props + rBracket).setName('listObj')
dictObj = (lCurly + propAttributes + rCurly).setName('dictObj')
panel_klass = (start + (dictOf(noSpaceWord + colon, (quotedWords ^ listObj ^ dictObj) + Optional(comma)))) 

propAttribute_str = "componentType: 'HMCServer'"
propAttribute_str2 = "header: _t('Build Level')"
prop_str = "{componentType: 'HMCServer', header: _t('Build Level')}"
list_str = "[{sortable: True, id: 'ServicePack'},\
             {id: 'buildLevel', sortable: False},\
             {name: 'uid'},\
             {name: 'name'},\
             {name: 'meta_type'},\
             {name: 'status'},\
             {name: 'severity'},\
             {name: 'usesMonitorAttribute'},\
             {name: 'monitor'},\
             {name: 'monitored'},\
             {name: 'serverName'},\
             {name: 'busId'},\
             {name: 'slotDesc'},\
             {name: 'IOPoolId'},\
             {name: 'Owner'},\
             {name: 'locking'}]"
dict_str = "{field: 'busId',\
             direction: 'asc'}"
panel_string = '''ZC.HMCServerPanel = Ext.extend(ZC.IBMComponentGridPanel, {
    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            componentType: 'HMCServer',
            autoExpandColumn: 'serialNumber',
            fields: [
                {name: 'servicePack'},
                {name: 'buildLevel'},
            ],
            columns: [
            {
                dataIndex: 'buildLevel',
                header: _t('Build Level'),
                sortable: true,
                id: 'buildLevel'
            },{
                dataIndex: 'servicePack',
                header: _t('Service Pack'),
                sortable: true,
                id: 'servicePack'
            }]
        });

        ZC.HMCServerPanel.superclass.constructor.call(
            this, config);
    }
'''

panel2_string = '''ZC.IODevicesPanel = Ext.extend(ZC.IBMComponentGridPanel, {
    constructor: function(config) {
        config = Ext.applyIf(config||{}, {
            componentType: 'IODevices',
            autoExpandColumn: 'name',
            sortInfo: {
                field: 'busId',
                direction: 'asc'
            },
            fields: [
                {name: 'uid'},
                {name: 'name'},
                {name: 'meta_type'},
                {name: 'status'},
                {name: 'severity'},
                {name: 'usesMonitorAttribute'},
                {name: 'monitor'},
                {name: 'monitored'},
                {name: 'serverName'},
                {name: 'busId'},
                {name: 'slotDesc'},
                {name: 'IOPoolId'},
                {name: 'Owner'},
                {name: 'locking'}
            ],
            columns: [{
                id: 'severity',
                dataIndex: 'severity',
                header: _t('Events'),
                renderer: Zenoss.render.severity,
                sortable: true,
                width: 70
            },{
                id: 'name',
                dataIndex: 'name',
                header: _t('Slot'),
                renderer: Zenoss.render.IBM_PowerServer_entityLinkFromGrid,
                sortable: true
            },{
                dataIndex: 'serverName',
                header: _t('Server Name'),
                sortable: true,
                width: 200,
                id: 'serverName'
            },{
                dataIndex: 'Owner',
                header: _t('Owner'),
                sortable: true,
                id: 'Owner'
            },{
                dataIndex: 'slotDesc',
                header: _t('Description'),
                sortable: true,
                width: 150,
                id: 'slotDesc'
            },{
                dataIndex: 'busId',
                header: _t('Bus Id'),
                sortable: true,
                id: 'busId'
            },{
                dataIndex: 'IOPoolId',
                header: _t('I / O Pool Id'),
                sortable: true,
                id: 'IOPoolId'
            },{
                id: 'monitored',
                dataIndex: 'monitored',
                header: _t('Monitored'),
                renderer: Zenoss.render.checkbox,
                sortable: true,
                width: 70
            },{
                id: 'locking',
                dataIndex: 'locking',
                header: _t('Locking'),
                renderer: Zenoss.render.locking_icons,
                width: 65
            }]
        });

        ZC.IODevicesPanel.superclass.constructor.call(
            this, config);
    }
});
'''
#propAttribute_result = propAttributes.searchString(propAttribute_str)
#propAttribute_result2 = propAttributes.searchString(propAttribute_str2)
#prop_result = prop.searchString(prop_str)
#list_result = listObj.searchString(list_str)
#dict_result = dictObj.searchString(dict_str)
#panel_result = panel_klass.searchString(panel_string)
#panel2_result = panel_klass.searchString(panel2_string)
#print propAttribute_result
#print propAttribute_result2
#print prop_result
#print list_result
#print dict_result
#print panel_result
#print panel2_result

def parse_panel_js(data, klasses):
    parsed_data = panel_klass.searchString(data)

    for klass in parsed_data:
        klass = dict(klass)

        klassId = klass['componentType']
        del(klass['componentType'])
        klass['monitoring_template'] = klassId

        if klassId not in klasses:
             klasses[klassId] = {}
        
        if 'properties' not in klasses[klassId]:
            klasses[klassId]['properties'] = {}

        if 'fields' in klass:
            del klass['fields']

        if 'columns' in klass:

            # Set the AutoExpandColumn if Found
            if 'autoExpandColumn' in klass:
                propId = klass['autoExpandColumn']

                if propId not in klasses[klassId]['properties']:
                    klasses[klassId]['properties'][propId] = {}

                klasses[klassId]['properties'][propId]['width'] = 'auto'
                del klass['autoExpandColumn']

            # Set the sortInfo if Found
            if 'sortInfo' in klass:
                propId = klass['sortInfo']['field']
                klasses[klassId]['properties'][propId]['sort_direction'] = klass['sortInfo']['direction']
                del klass['sortInfo']

            for p in klass['columns']:
                data = {k:v for (k,v) in p.items() if not k.startswith('//')}
                propId = data['id']

                # zpl provides these automatically
                if propId in ['severity', 'monitored', 'locking']:
                    continue 

                del(data['id'])

                if 'sortable' in data:
                    #zpl defaults to true
                    data['sortable'] == 'true'
                    del(data['sortable'])

                for key in ['dataIndex', 'header']:
                    if key == 'header':
                        data['label'] = data['header']
                    if key in data:
                        del(data[key])

                data['grid_display'] = True

                for key,val in data.items():
                    if propId not in klasses[klassId]['properties']:
                        klasses[klassId]['properties'][propId] = {}
                    klasses[klassId]['properties'][propId][key] = val
        else:
            print "Warning %s has no columns. Most likely the result of a parsing error." % klassId
    return klasses

def parse_label_js(data, klasses):
    results = klass_labels.searchString(data)
    for klass in results:
        klassId = klass[0]
        if klassId not in klasses:
            klasses[klassId] = {}
        klasses[klassId]['label'] = klass[1][0]
        klasses[klassId]['plural_label'] = klass[1][1]
    return klasses

def parse_class_ast(data, class_id, klasses, relations):
    ast_klasses = klasses
    ast_relations = relations
    tree = ast.parse(data)
    for node in tree.body:
        if isinstance(node, ClassDef):
            # If the property is in the IInfo its displayed in the panel
            if "I%sInfo" % class_id == node.name:
                if class_id not in ast_klasses:
                    ast_klasses[class_id] = {}
                if 'properties' not in ast_klasses[class_id]:
                    ast_klasses[class_id]['properties'] = {}
                for item in node.body:
                    for target in item.targets:
                        if target.id not in ast_klasses[class_id]['properties']:
                            ast_klasses[class_id]['properties'][target.id] = {}
                        ast_klasses[class_id]['properties'][target.id]['details_display'] = True
            if 'Info' not in node.name and node.name in class_id:
                if node.name not in ast_klasses:
                    ast_klasses[node.name] = {}
                if 'properties' not in ast_klasses[node.name]:
                    ast_klasses[node.name]['properties'] = {}

                # Parent Classes = node.bases[0].id
                for item in node.body:
                    if isinstance(item, Assign):
                        value = item.value
                        if isinstance(value, Name):
                            value = value.id
                        if isinstance(value, Str):
                            value = value.s
                        if isinstance(value, (Dict, Call)):
                            'We dont care about dicts or functions'
                            break
                        for target in item.targets:
                            if target.id in ['factory_type_information']:
                                break

                            # Relations
                            if target.id == '_relations':
                                if isinstance(value, BinOp):
                                    # handle this recursively .. eg tuple may
                                    # be ordered funkily... but for now lets
                                    # assume a sane ordering.
                                    if isinstance(value.right, Tuple):
                                        for item in value.right.elts:
                                            lclass = class_id
                                            lrelname = item.elts[0].s
                                            lreltype = item.elts[1].func.id
                                            rreltype = item.elts[1].args[0].id
                                            rclass = item.elts[1].args[1].s.split('.')[-1]
                                            rrelname = item.elts[1].args[2].s
                                            rel = RelationFactory(lclass, lrelname, lreltype, rreltype, rclass, rrelname)
                                            if str(rel) in [str(x) for x in ast_relations] or str(rel.reverse()) in [str(x) for x in ast_relations]:
                                                pass
                                            else:
                                                ast_relations.append(rel)
                                break

                            # Zope Properties
                            if target.id == '_properties':
                                if isinstance(value, BinOp):
                                    if isinstance(value.right, Tuple):
                                        value = ast.literal_eval(value.right)
                                else:
                                    # ToDo handle an object ... or left side
                                    # stuff
                                    value = {}

                                for p in value:
                                    prop_id=p['id']
                                    del(p['id'])
                                    del(p['mode'])
                                    if p['type'] == 'string':
                                        del(p['type'])
                                    if prop_id not in ast_klasses[node.name]['properties']:
                                        ast_klasses[node.name]['properties'][prop_id] = {}
                                    for key in p:
                                        ast_klasses[node.name]['properties'][prop_id][key] = p[key]
                            else:
                                if target.id not in ast_klasses[node.name]['properties']:
                                    ast_klasses[node.name]['properties'][target.id] = {}
                                if not value == 'None':
                                    ast_klasses[node.name]['properties'][target.id]['default'] = value

            # Ignore classes that didn't specify meta_type .. sort of hacky
            # clear out the meta_type and portal_type key if set.
            if node.name in ast_klasses:
                if 'properties' in ast_klasses[node.name]:
                    if 'meta_type' not in ast_klasses[node.name]['properties']:
                        del(ast_klasses[node.name])
                    else:
                        for prop in ['meta_type', 'portal_type']:
                            if prop in ast_klasses[node.name]['properties']:
                                del(ast_klasses[node.name]['properties'][prop])


    return ast_klasses, ast_relations

klasses = {}
relations = []
python_files = glob.glob('*.py')
for pf in python_files:
    with open(pf, 'r') as fh:
        data = fh.read()
        class_id = os.path.basename(pf).rstrip('.py')
        klasses, relations = parse_class_ast(data, class_id, klasses, relations)

# process each file as it is found:
for filename in find_files('.', '*.js'):
    with open(filename, 'r') as fh:
        data = fh.read()
        klasses = parse_panel_js(data, klasses)
        klasses = parse_label_js(data, klasses)

print print_relationships_yuml(relations)
pprint(klasses)
