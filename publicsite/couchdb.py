import httplib, simplejson  # http:#cheeseshop.python.org/pypi/simplejson
                            # Here only used for prettyprinting

def prettyPrint(s):
    """Prettyprints the json response of an HTTPResponse object"""
    return s.read()

#
# Document and document set objects
#

class Doc(dict):
    
    def __init__(self):
        super(dict, self).__init__()
        self.id = None
        self.key = None
    
class DocSet(list):
    
    def __init__(self, offset=None, docs=None):
        super(list, self).__init__()
        self.offset = offset
        
#
# Couch access object
#

class Couch(object):
    """Basic wrapper class for operations on a couchDB"""

    def __init__(self, host, port=5984, options=None, handlers=None):
        self.host = host
        self.port = port        
        if not handlers:
            handlers = { }
        self.handlers = handlers

    def connect(self):
        return httplib.HTTPConnection(self.host, self.port) # No close()

    # Database operations

    def createDb(self, dbName):
        """Creates a new database on the server"""

        r = self.put(''.join(['/',dbName,'/']), "")
        prettyPrint(r)

    def deleteDb(self, dbName):
        """Deletes the database on the server"""

        r = self.delete(''.join(['/',dbName,'/']))
        prettyPrint(r)

    def listDb(self):
        """List the databases on the server"""

        prettyPrint(self.get('/_all_dbs'))

    def infoDb(self, dbName):
        """Returns info about the couchDB"""
        r = self.get(''.join(['/', dbName, '/']))
        prettyPrint(r)

    # Document operations

    def listDoc(self, dbName):
        """List all documents in a given database"""

        r = self.get(''.join(['/', dbName, '/', '_all_docs']))
        prettyPrint(r)
        
        
    def openDoc(self, dbName, docId):
        """Open a document in a given database"""
        r = self.get(''.join(['/', dbName, '/', docId,]))
        prettyPrint(r)

    def saveDoc(self, dbName, body, docId=None):
        """Save/create a document to/in a given database"""
        if docId:
            r = self.put(''.join(['/', dbName, '/', docId]), body)
        else:
            r = self.post(''.join(['/', dbName, '/']), body)
        prettyPrint(r)

    def deleteDoc(self, dbName, docId):     # XXX Crashed if resource is non-existent; not so for DELETE on db. Bug?
        r = self.delete(''.join(['/', dbName, '/', docId]))
        prettyPrint(r)

    def adHoc(self, dbName, doc, rowcount, options, raw=False):
        r = self.post(''.join(['/', dbName, '/_temp_view/?count=%s&%s' % (rowcount, options)]), doc)
        if raw:
            return r.read()
        return self.process_response(r)
        
    # Build DocSet for response
    
    def process_response(self, response):
        try:
            results = simplejson.loads(response.read())
            ds = DocSet(offset=results.get('offset', 0))
            for row in results.get('rows', None):
                d = Doc()
                d.id = row.get('id', None)
                d.key = row.get('key', None)
                for key, value in row.get('value', { }).items():
                    key = key.lower()
                    if hasattr(value, 'count') and len(value) == 1 and value[0] == '':
                        value = None
                    elif value == '':
                        value = None
                    if self.handlers.has_key(key):
                        self.handlers[key](key, value, d)
                    else:
                        d[key] = value
                ds.append(d)
        except:
            ds = None
        return ds

    # Basic http methods

    def get(self, uri):
        c = self.connect()
        headers = {"Accept": "application/json"}
        c.request("GET", uri, None, headers)
        return c.getresponse()

    def post(self, uri, body):
        c = self.connect()
        headers = {"Content-type": "text/javascript"}
        c.request('POST', uri, body, headers)
        return c.getresponse()

    def put(self, uri, body):
        c = self.connect()
        if len(body) > 0:
            headers = {"Content-type": "application/json"}
            c.request("PUT", uri, body, headers)
        else:
            c.request("PUT", uri, body)
        return c.getresponse()

    def delete(self, uri):
        c = self.connect()
        c.request("DELETE", uri)
        return c.getresponse()