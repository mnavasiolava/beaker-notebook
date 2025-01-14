# Copyright 2014 TWO SIGMA OPEN SOURCE, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

if sys.version_info >= (3,0):
    raise RuntimeError('Python3 was found when trying to start Python2. _beaker_python_mismatch_')

import os, urllib, urllib2, json, pandas, numpy, IPython, datetime, calendar, math, traceback, types, time
from IPython.utils.traitlets import Unicode

class OutputContainer:
    def __init__(self):
        self.items = []
    def clear(self):
        self.items = [ ]
    def addItem(self, obj):
        self.items.append(obj)
    def getItems(self):
        return self.items

class BeakerCodeCell:
    def __init__(self, cellId, evaluatorId):
        self.cellId = cellId
        self.evaluatorId = evaluatorId
        self.code = ''
        self.outputtype = ''
        self.output = None
        self.tags = ''
    def getCellId(self):
        return self.cellId
    def getEvaluatorId(self):
        return self.evaluatorId
    def getCode(self):
        return self.code
    def getOutputType(self):
        return self.outputtype
    def getOutput(self):
        return self.output
    def getTags(self):
        return self.tags

def convertTypeName(typ):
    if typ.startswith("float"):
        return "double"
    if typ.startswith("int") or typ.startswith("uint") or typ.startswith("short") or typ.startswith("ushort") or typ.startswith("long") or typ.startswith("ulong"):
        return "integer"
    if typ.startswith("bool"):
        return "boolean"
    if typ.startswith("date") or typ.startswith("Time"):
        return "datetime"
    return "string"
    
def isPrimitiveType(typ):
    if typ.startswith("float"):
        return True
    if typ.startswith("int") or typ.startswith("uint") or typ.startswith("short") or typ.startswith("ushort") or typ.startswith("long") or typ.startswith("ulong"):
        return True
    if typ.startswith("bool"):
        return True
    if typ.startswith("date") or typ.startswith("Time"):
        return True
    if typ.startswith("str"):
        return True
    return False

def isListOfMaps(data):
    if type(data) != list:
        return False
    for w in data:
        if type(w) != dict:
            return False
        for v in w.itervalues():
            if not isPrimitiveType(type(v).__name__):
                return False
    return True

def isDictionary(data):
    if type(data) != dict:
        return False
    for v in data.itervalues():
        if not isPrimitiveType(type(v).__name__):
            return False
    return True

def transformNaN(obj):
    if not isinstance(obj, types.FloatType):
        return obj
    if math.isnan(obj):
        return "Nan";
    if math.isinf(obj):
        if obj>0:
            return "Infinity"
        else:
            return "-Infinity"
    return obj

def transformNaNs(obj):
    for x in range(0,len(obj)):
        i = obj[x];
        if not isinstance(i, types.FloatType):
            continue
        if math.isnan(i):
            obj[x] = "NaN";
        if math.isinf(i):
            if i>0:
                obj[x] = "Infinity"
            else:
                obj[x] = "-Infinity"

def fixNaNBack(obj):
    if not isinstance(obj, types.StringType):
        return obj
    if obj == "NaN":
        return float('nan')
    if obj == "Infinity":
        return float('inf')
    if obj == "-Infinity":
        return float('-inf')
    return obj

def fixNaNsBack(obj):
    for x in range(0,len(obj)):
        i = obj[x];
        if not isinstance(i, types.StringType):
            continue
        if i == "NaN":
            obj[x] = float('nan')
        if i == "Infinity":
            obj[x] = float('inf')
        if i == "-Infinity":
            obj[x] = float('-inf')

def transform(obj):
    if type(obj) == unicode:
        return str(obj)
    if isListOfMaps(obj):
        out = {}
        out['type'] = "TableDisplay"
        out['subtype'] = "ListOfMaps"
        cols = []
        for l in obj:
            cols.extend(l.iterkeys())
        cols = list(set(cols))
        out['columnNames'] = cols
        vals = []
        for l in obj:
            row = []
            for r in cols:
                if r in l:
                    row.append(transformNR(l[r]))
                else:
                    row.append('')
            vals.append(row)
        out['values'] = vals
        return out
    if isDictionary(obj):
        out = {}
        out['type'] = "TableDisplay"
        out['subtype'] = "Dictionary"
        out['columnNames'] = [ "Key", "Value" ]
        values = []
        for k,v in obj.iteritems():
            values.append( [k, transformNR(v)] )
        out['values'] = values
        return out
    if type(obj) == dict:
        out = {}
        for k,v in obj.iteritems():
            out[k] = transformNR(v)
        return out
    if type(obj) == list:
        out = []
        for v in obj:
            out.append(transformNR(v))
        return out
    if isinstance(obj, OutputContainer):
        out = {}
        out['type'] = "OutputContainer"
        items = []
        for v in obj.getItems():
            items.append(transform(v))
        out['items'] = items
        return out
    if isinstance(obj, BeakerCodeCell):
        out = {}
        out['type'] = "BeakerCodeCell"
        out['cellId'] = obj.getCellId()
        out['evaluatorId'] = obj.getEvaluatorId()
        out['code'] = obj.getCode()
        out['outputtype'] = obj.getOutputType()
        out['output'] = transform(obj.getOutput())
        out['tags'] = obj.getTags()
        return out
    return transformNaN(obj)

def transformNR(obj):
    if type(obj) == unicode:
        return str(obj)
    if type(obj) == dict:
        out = {}
        for k,v in obj.iteritems():
            out[k] = transformNR(v)
        return out
    if type(obj) == list:
        out = []
        for v in obj:
            out.append(transformNR(v))
        return out
    if isinstance(obj, OutputContainer):
        out = {}
        out['type'] = "OutputContainer"
        items = []
        for v in obj.getItems():
            items.append(transform(v))
        out['items'] = items
        return out
    if isinstance(obj, BeakerCodeCell):
        out = {}
        out['type'] = "BeakerCodeCell"
        out['cellId'] = obj.getCellId()
        out['evaluatorId'] = obj.getEvaluatorId()
        out['code'] = obj.getCode()
        out['outputtype'] = obj.getOutputType()
        out['output'] = transform(obj.getOutput())
        out['tags'] = obj.getTags()
        return out
    return transformNaN(obj)

def transformBack(obj):
    if type(obj) == dict:
        out = {}
        for k,v in obj.iteritems():
            out[str(k)] = transformBack(v)
        if "type" in out:
            if out['type'] == "BeakerCodeCell":
                c = BeakerCodeCell(out['cellId'], out['evaluatorId'])
                if 'code' in out:
                    c.code = out['code']
                if 'outputtype' in out:
                    c.outputtype = out['outputtype']
                if 'output' in out:
                    c.output = transformBack(out['output'])
                if 'tags' in out:
                    c.tags = out['tags']
                return c
            if out['type'] == "OutputContainer":
                c = OutputContainer()
                if 'items' in out:
                    for i in out['items']:
                        c.addItem(i)
                return c;
            if out['type'] == "Date":
                return datetime.datetime.fromtimestamp(out["timestamp"]/1000)
            if out['type'] == "TableDisplay":
                if 'subtype' in out:
                    if out['subtype'] == "Dictionary":
                        out2 = { }
                        for r in out['values']:
                            out2[r[0]] = fixNaNBack(r[1])
                        if out['columnNames'][0] == "Index":
                            return pandas.Series(out2)
                        return out2
                    if out['subtype'] == "Matrix":
                        vals = out['values']
                        fixNaNsBack(vals)
                        return numpy.matrix(vals)
                    if out['subtype'] == "ListOfMaps":
                        out2 = []
                        cnames = out['columnNames']
                        for r in out['values']:
                            out3 = { }
                            for i in range(len(cnames)):
                                if r[i] != '':
                                    out3[ cnames[i] ] = r[i]
                            out2.append(out3)
                        return out2
                # transform to dataframe
                if ('hasIndex' in out) and (out['hasIndex'] == "true"):
                    # first column becomes the index
                    vals = out['values']
                    cnames = out['columnNames'][1:]
                    index = []
                    for x in range(0,len(vals)):
                        index.append(transformBack(vals[x][0]))
                        v = vals[x][1:]
                        fixNaNsBack(v)
                        vals[x] = v
                    return pandas.DataFrame(data=vals, columns=cnames, index=index)
                else:
                    vals = out['values']
                    cnames = out['columnNames']
                    for x in range(0,len(vals)):
                        v = vals[x]
                        fixNaNsBack(v)
                        vals[x] = v
                    return pandas.DataFrame(data=vals, columns=cnames)
        return out
    if type(obj) == list:
        out = []
        for v in obj:
            out.append(transformBack(v))
        return out
    try:
        if type(obj) == unicode:
            obj = str(obj)
    except Exception as e:
        return obj
    return obj

# should be inner class to Beaker
class DataFrameEncoder(json.JSONEncoder):
    def default(self, obj):
        # similarly handle Panels.
        # make this extensible by the user to handle their own types.
        if isinstance(obj, numpy.generic):
            return transformNaN(obj.item())
        if isinstance(obj, numpy.ndarray) and obj.ndim == 2:
            out = {}
            out['type'] = "TableDisplay"
            out['subtype'] = "Matrix"
            cols = [ ]
            for i in range(obj.shape[1]):
                cols.append( "c" + str(i) )
            out['columnNames'] = cols
            vars = obj.tolist()
            for x in range(0,len(vars)):
                transformNaNs(vars[x])
            out['values'] = vars
            return out
        if isinstance(obj, numpy.ndarray):
            ret = obj.tolist()
            transformNaNs(ret)
            return ret
        if type(obj) == datetime.datetime or type(obj) == datetime.date or type(obj).__name__ == 'Timestamp':
            out = {}
            out['type'] = "Date"
            out['timestamp'] = time.mktime(obj.timetuple()) * 1000
            return out
        if type(obj) == pandas.core.frame.DataFrame:
            out = {}
            out['type'] = "TableDisplay"
            out['subtype'] = "TableDisplay"
            out['hasIndex'] = "true"
            out['columnNames'] = ['Index'] + obj.columns.tolist()
            vals = obj.values.tolist()
            idx = obj.index.tolist()
            for x in range(0,len(vals)):
                vals[x] = [ idx[x] ] + vals[x]
            ty = []
            num = len(obj.columns.tolist())
            x = 0;
            for x in range(0,len(vals)):
                transformNaNs(vals[x])
            for x in range(0,num+1):
              	ty.append(convertTypeName(type(vals[0][x]).__name__))
            out['types'] = ty
            out['values'] = vals
            return out
        if type(obj) == pandas.core.series.Series:
            basict = True
            for i in range(len(obj)):
                if not isPrimitiveType(type(obj[i]).__name__):
                    basict = False
                    break
            if basict:
                out = {}
                out['type'] = "TableDisplay"
                out['subtype'] = "Dictionary"
                out['columnNames'] = [ "Index", "Value" ]
                values = []
                for k,v in obj.iteritems():
                    values.append( [k, transform(v)] )
                out['values'] = values
                return out
            return obj.to_dict()
        return json.JSONEncoder.default(self, obj)

class MyJSONFormatter(IPython.core.formatters.BaseFormatter):
    format_type = Unicode('application/json')
    def __call__(self, obj):
        try:
            obj = transform(obj)
            return json.dumps(obj, cls=DataFrameEncoder)
        except Exception as e:
            #print(e)
            #traceback.print_exc()
            return None

class Beaker:
    """Runtime support for Python code in Beaker."""
    session_id = ''
    core_url = '127.0.0.1:' + os.environ['beaker_core_port']
    _beaker_password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    _beaker_password_mgr.add_password(None, core_url, 'beaker',
                              os.environ['beaker_core_password'])
    _beaker_url_opener = urllib2.build_opener(urllib2.HTTPBasicAuthHandler(_beaker_password_mgr), urllib2.ProxyHandler({}))

    def set4(self, var, val, unset, sync):
        args = {'name': var, 'session':self.session_id, 'sync':sync}
        if not unset:
            val = transform(val)
            args['value'] = json.dumps(val, cls=DataFrameEncoder)
        req = urllib2.Request('http://' + self.core_url + '/rest/namespace/set',
                              urllib.urlencode(args))
        conn = self._beaker_url_opener.open(req)
        reply = conn.read()
        if reply != 'ok':
            raise NameError(reply)
  
    def get(self, var):
        result = self._getRaw(var)
        if not result['defined']:
            raise NameError('name \'' + var + '\' is not defined in notebook namespace')
        return transformBack(result['value'])

    def _getRaw(self, var):
        req = urllib2.Request('http://' + self.core_url + '/rest/namespace/get?' +
                              urllib.urlencode({'name': var, 'session': self.session_id}))
        conn = self._beaker_url_opener.open(req)
        result = json.loads(conn.read())
        return result

    def set_session(self, id):
        self.session_id = id

    def register_output(self):
        ip = IPython.InteractiveShell.instance()
        ip.display_formatter.formatters['application/json'] = MyJSONFormatter(parent=ip.display_formatter)

    def set(self, var, val):
        return self.set4(var, val, False, True)

    def unset(self, var):
        return self.set4(var, None, True, True)

    def isDefined(self, var):
        return self._getRaw(var)['defined']

    def createOutputContainer(self):
        return OutputContainer()
    
    def showProgressUpdate(self):
        return "WARNING: python language plugin does not support progress updates"

    def evaluate(self,filter):
        args = {'filter': filter, 'session':self.session_id}
        req = urllib2.Request('http://' + self.core_url + '/rest/notebookctrl/evaluate',
                              urllib.urlencode(args))
        conn = self._beaker_url_opener.open(req)
        result = json.loads(conn.read())
        return transformBack(result)

    def evaluateCode(self, evaluator,code):
        args = {'evaluator': evaluator, 'code' : code, 'session':self.session_id}
        req = urllib2.Request('http://' + self.core_url + '/rest/notebookctrl/evaluateCode',
                              urllib.urlencode(args))
        conn = self._beaker_url_opener.open(req)
        result = json.loads(conn.read())
        return transformBack(result)

    def showStatus(self,msg):
        args = {'msg': msg, 'session':self.session_id}
        req = urllib2.Request('http://' + self.core_url + '/rest/notebookctrl/showStatus',
                              urllib.urlencode(args))
        conn = self._beaker_url_opener.open(req)
        result = conn.read()
        return result=="true"

    def clearStatus(self,msg):
        args = {'msg': msg, 'session':self.session_id}
        req = urllib2.Request('http://' + self.core_url + '/rest/notebookctrl/clearStatus',
                              urllib.urlencode(args))
        conn = self._beaker_url_opener.open(req)
        result = conn.read()
        return result=="true"

    def showTransientStatus(self,msg):
        args = {'msg': msg, 'session':self.session_id}
        req = urllib2.Request('http://' + self.core_url + '/rest/notebookctrl/showTransientStatus',
                              urllib.urlencode(args))
        conn = self._beaker_url_opener.open(req)
        result = conn.read()
        return result=="true"

    def getEvaluators(self):
        req = urllib2.Request('http://' + self.core_url + '/rest/notebookctrl/getEvaluators?' + 
                              urllib.urlencode({'session':self.session_id}))
        conn = self._beaker_url_opener.open(req)
        result = json.loads(conn.read())
        return transformBack(result)

    def getVersion(self):
        req = urllib2.Request('http://' + self.core_url + '/rest/util/version?' + urllib.urlencode({'session':self.session_id}))
        conn = self._beaker_url_opener.open(req)
        return transformBack(conn.read().decode())

    def getVersionNumber(self):
        req = urllib2.Request('http://' + self.core_url + '/rest/util/getVersionInfo?' + urllib.urlencode({'session':self.session_id}))
        conn = self._beaker_url_opener.open(req)
        result = json.loads(conn.read().decode())
        return transformBack(result['version'])

    def getCodeCells(self,filter):
        req = urllib2.Request('http://' + self.core_url + '/rest/notebookctrl/getCodeCells?' + 
                              urllib.urlencode({'session':self.session_id, 'filter':filter}))
        conn = self._beaker_url_opener.open(req)
        result = json.loads(conn.read())
        return transformBack(result)

    def setCodeCellBody(self,name,body):
        args = {'name': name, 'body':body, 'session':self.session_id}
        req = urllib2.Request('http://' + self.core_url + '/rest/notebookctrl/setCodeCellBody',
                              urllib.urlencode(args))
        conn = self._beaker_url_opener.open(req)
        result = conn.read()
        return result=="true"

    def setCodeCellEvaluator(self,name,evaluator):
        args = {'name': name, 'evaluator':evaluator, 'session':self.session_id}
        req = urllib2.Request('http://' + self.core_url + '/rest/notebookctrl/setCodeCellEvaluator',
                              urllib.urlencode(args))
        conn = self._beaker_url_opener.open(req)
        result = conn.read()
        return result=="true"

    def setCodeCellTags(self,name,tags):
        args = {'name': name, 'tags':tags, 'session':self.session_id}
        req = urllib2.Request('http://' + self.core_url + '/rest/notebookctrl/setCodeCellTags',
                              urllib.urlencode(args))
        conn = self._beaker_url_opener.open(req)
        result = conn.read()
        return result=="true"

    def __setattr__(self, name, value):
        if 'session_id' == name:
            self.__dict__['session_id'] = value
            return
        return self.set(name, value)

    def __getattr__(self, name):
        return self.get(name)

    def __contains__(self, name):
        return self.isDefined(name)

    def __delattr__(self, name):
        return self.unset(name)