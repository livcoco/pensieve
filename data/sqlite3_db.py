#!/usr/bin/python3
'''
history:
12/19 - eliminate tableInits?
12/19/18 - need to change categoryTable:preNodeId to preCatId
'''

import sqlite3
import multiprocessing
import time
from collections import OrderedDict

class DatabaseInterface:
    '''
    Concepts:
      - category:
      - node:
      - path:
      - alias:
      - pathRev:
    Reads and writes data to a set of tables which keep track of:
      - categories of notes
      - individual nodes within the categories
      - parent child relationships between both categories and individual nodes.
    The database maintains all historical versions so notes referring to an old path do not have to be updated 
    '''
    def __init__(self, database_path_and_file_name, lock, in_memory = False, create_new_database = False):
        if in_memory:
            self.db = sqlite3.connect(":memory:")
            self.db.isolation_level = None
        else:
            self.db = sqlite3.connect(database_path_and_file_name)
            self.db.isolation_level = None
            self.db.execute('PRAGMA journal_mode = MEMORY')
            self.dbCursor = self.db.cursor()
            self.lock = lock
        #todo = 'id INTEGER PRIMARY KEY UNIQUE NOT NULL AUTOINCREMENT, noteText BLOB'
        #newIdea = 'id INTEGER PRIMARY KEY AUTOINCREMENT, noteText BLOB'
        #understanding = 'id INTEGER PRIMARY KEY UNIQUE NOT NULL, noteText BLOB'
        #textEdit = 'id INTEGER PRIMARY KEY UNIQUE NOT NULL, noteText BLOB'
        #videoEdit = 'id INTEGER PRIMARY KEY UNIQUE NOT NULL, noteText BLOB'
        #audioEdit = 'id INTEGER PRIMARY KEY UNIQUE NOT NULL, noteText BLOB'
        self.columnSpecs = {
            'nodes'   : 'nodeId INTEGER, pathRev INTEGER, name BLOB, dx INTEGER, dy INTEGER, lastPathRev INTEGER, PRIMARY KEY (nodeId, pathRev)',
            'preNodes': 'nodeId INTEGER, pathRev INTEGER, preNodeId INTEGER, prePathRev INTEGER, categoryID INTEGER, nameAlias BLOB, lastPrePathRev INTEGER, PRIMARY KEY (nodeID, pathRev, preNodeId, prePathRev)',
            'categories': 'categoryId INTEGER, preCatId INTEGER, catName BLOB, PRIMARY KEY(categoryId, preCatId)',
        #    'newIdeas': 'id INTEGER PRIMARY KEY AUTOINCREMENT, noteText BLOB, date BLOB, owner BLOB',
        #    'toDo'    : 'id INTEGER PRIMARY KEY AUTOINCREMENT, noteText BLOB, date BLOB, owner BLOB, completeByDate BLOB'
        }
        self.sqlAdds = {
            'nodes'   : 'INSERT INTO nodes (nodeId, pathRev, name, dx, dy, lastPathRev) VALUES (?, ?, ?, ?, ?, ?)',
            'preNodes': 'INSERT INTO preNodes (nodeId, pathRev, preNodeId, prePathRev, categoryID, nameAlias, lastPrePathRev) VALUES (?, ?, ?, ?, ?, ?, ?)',
            'categories':'INSERT INTO categories (categoryId, preCatId, catName) VALUES (?, ?, ?)',
        }
        self.sqlDumps = {
            'nodes' : 'SELECT nodeId, pathRev, name, dx, dy, lastPathRev from nodes',
            'preNodes' : 'SELECT nodeId, pathRev, preNodeId, prePathRev, categoryID, nameAlias, lastPrePathRev from preNodes',
            'categories' : 'SELECT categoryId, preCatId, catName from categories',
        }
        self.tableInits = {
            'nodes'   : (0, 0, None, None, None, None),
            'preNodes'   : (0, 0, None, None, None, None, None),
            'categories' : (0, None, None),
        }
        if create_new_database:
            for tableName in self.columnSpecs.keys():
                columnSpec = self.columnSpecs[tableName]
                entries = columnSpec.split()
                idName = entries[0]
                try:
                    self.dbCursor.execute('select MAX(' + idName + ') FROM ' + tableName)
                    assert False, 'I was asked to create a new database, but there is already a database with something in it'
                except sqlite3.OperationalError:
                    self._addTable(tableName)

    def getNodeInfo(self, node_name):
        '''
        returns all instances of node_name both for standard name and aliases. 
        if node_name exists:
          return (
                  (nodeIdA, nodeName, categoryId1, categoryName1, alias1, preNodeId1, preNodeName1, 
                  (nodeIdA, nodeName, categoryId2, categoryName2, alias2, preNodeId2, preNodeName2,
                  (nodeIdB, nodeName, categoryId3, categoryName3, alias3, preNodeId3, preNodeName3,
                  ... ,
                 )
        else:
          return ()
        '''

        # get the data from 'nodes' for this node name
        nodesData = []
        cursor = self.dbCursor.execute(r'SELECT nodeId, pathRev, lastPathRev FROM nodes WHERE name == "' + node_name + '"')
        while True:
            data = cursor.fetchone()
            if not data:
                break
            nodesData.append(data)
        #find only the latest valid revision data
        latestNodesData = OrderedDict() #this way we can keep them in non-random order
        obsoleteNodeIds = set()
        for (nodeId, pathRev, lastPathRev) in nodesData:
            if lastPathRev:
                obsoleteNodeIds.add(lastPathRev)
                continue #indicates this is an obsolete node
            if nodeId not in latestNodesData.keys():
                latestNodesData[nodeId] = [node_name, pathRev]
            elif pathRev > latestNodesData[nodeId]:
                latestNodesData[nodeId][1] = pathRev
        # eliminate obsolete nodes
        for obsoleteNodeId in obsoleteNodeIds:
            latestNodesData.pop(obsoleteNodeId)

        # the node_name could be an alias, so get the data from preNodes
        preNodesData = []
        cursor = self.dbCursor.execute(r'SELECT nodeId, pathRev, preNodeId, prePathRev, lastPrePathRev FROM preNodes WHERE nameAlias == "' + node_name + '"')
        while True:
            data = cursor.fetchone()
            if not data:
                break
            preNodesData.append(data)

        #find only the latest valid revision data        
        latestPreNodesData = OrderedDict() #this way we can keep them in non-random order
        obsoletePreNodeIds = set()
        for (nodeId, pathRev, preNodeId, prePathRev, lastPrePathRev) in preNodesData:
            if lastPrePathRev:
                obsoletePreNodeIds.add(preNodeId)
                continue
            if preNodeId not in latestPreNodesData:
                latestPreNodesData[preNodeId] = prePathRev
            elif prePathRev > latestsPreNodesData[preNodeId]:
                latestPreNodesData[preNodeId] = prePathRev
        # eliminate obsolete preNodes
        for obsoletePreNodeId in obsoletePreNodeIds:
            latestPreNodesData.pop(obsoleteNodeId)

        # get the preNodes names
        for preNodeId in latestPreNodesData.keys():
            prePathRev = latestPreNodesData[preNodeId]
            cursor = self.dbCursor.execute(r'SELECT name FROM nodes WHERE nodeId == ' + str(preNodeId) + ' AND pathRev == ' + str(prePathRev))
            (name,) = cursor.fetchone()
            latestPreNodesData[preNodeId] = [name, preNodeId]
        
        # combine the latestPreNodesData with the latestNodesData
        for preNodeId in latestPreNodesData.keys():
            latestNodesData[preNodeId] = latestPreNodesData[preNodeId]
            
        # get data from preNodes table
        preNodesData = {}
        retData = []
        for nodeId in latestNodesData.keys():
            (name, pathRev) = latestNodesData[nodeId]
            cursor = self.dbCursor.execute(r'SELECT preNodeId, prePathRev, categoryId, nameAlias from preNodes WHERE nodeId == "' + str(nodeId) + '" AND pathRev == "' + str(pathRev) + '"')
            while True:
                data = cursor.fetchone()
                if not data:
                    break
                (preNodeId, prePathRev, categoryId, nameAlias) = data
                #                                        catName                    preNodeName
                retData.append( [nodeId, name, categoryId, None, nameAlias, preNodeId, None] )

        #get the preNode names
        for idx in range(len(retData)):
            (nodeId, name, categoryId, categoryName, nameAlias, preNodeId, preNodeName) = retData[idx]
            cursor = self.dbCursor.execute(r'SELECT name from nodes WHERE nodeId == ' + str(preNodeId))
            (name,) = cursor.fetchone()
            retData[idx][6] = name
            
        # get the preCategory names
        for idx in range(len(retData)):
            (nodeId, name, categoryId, categoryName, nameAlias, preNodeId, preNodeName) = retData[idx]
            cursor = self.dbCursor.execute(r'SELECT catName from categories WHERE categoryId == ' + str(categoryId))
            (categoryName,) = cursor.fetchone()
            retData[idx][3] = categoryName

        for idx in range(len(retData)):
            retData[idx] = tuple(retData[idx])

        return tuple(retData)
    
    def addNodesToCategory(self, nodes, category_name = None, category_id = None, pre_node_name = None, pre_node_id = None):
        '''
        do not create a new category, reuse an existing category, just extend it with new nodes
        calls addNodes with category_id specified.
        '''
        # get the category id and pass it to addNodes which will know to add to the category since it got the category id
        if category_id != None:
            categoryId = category_id
        else:
            cursor = self.dbCursor.execute('SELECT categoryID FROM categories WHERE catName == \"' + str(category_name) + '\"')
            data = cursor.fetchone()
            if data:
                (categoryId,) = data
            else:
                return False
            data2 = cursor.fetchone()
            if data2:
                # there are two different categories with the same name.  The user will need to figure out which one he wants
                raise AmbiguousNameException()
        self.addNodes(nodes, category_name, categoryId, pre_node_name, pre_node_id)
        
    def addNodes(self, nodes, category_name = None, category_id = None, pre_node_name = None, pre_node_id = None):
        '''
        add the nodes to the table nodes, add information to preNodes, and if the category is new, add a new category
        nodes: a list of nodes to be added to the nodes table and the preNodes table
        category: the category for the preNodes table
        pre_node_name, pre_node_id:
          None, None: No preNode is specified, which is OK, just leave preNode data blank
          'name', None: a name is specified, but no nodeId, so look up the nodeId corresponding to the name
          None, nodeId: the nodeId is specified, so use that directly
          'name', nodeId: both are specified, validate the name matches the nodeId
        raises AmbiguousNameException if the category_name or pre_node_name is given without its corresponding id, and there are more than one id with the same name.
        '''
        show = False
        if show: print('in addNodes() with nodes', nodes, ', category_name', category_name, ', category_id', category_id, ', pre_node_name', pre_node_name, ', pre_node_id', pre_node_id)

        # get the max nodeId and pathRev so we can add new nodes with unique ids and assign them a new pathRev
        nodesColumnSpec = self.columnSpecs['nodes']
        entries = nodesColumnSpec.split()
        nodesPrimaryKey1 = entries[-2].replace('(','').replace(',','')
        nodesPrimaryKey2 = entries[-1].replace(')','').replace(',','')
        if show: print('  nodes table primary keys:', nodesPrimaryKey1, nodesPrimaryKey2)
        cursor = self.dbCursor.execute('SELECT MAX(' + nodesPrimaryKey1 + ') FROM nodes')
        (nodeId,) = cursor.fetchone()
        nodeId += 1
        cursor = self.dbCursor.execute('SELECT MAX(' + nodesPrimaryKey2 + ') FROM nodes')
        (pathRev,) = cursor.fetchone()
        pathRev += 1
            
        # find the preNodeId if possible or raise an AmbiguousNameException
        lastPathRev = None
        if pre_node_name == None and pre_node_id == None:
            preNodeId = None
            prePathRev = None
        elif pre_node_id != None:
            preNodeId = pre_node_id
            cursor = self.dbCursor.execute('SELECT MAX(pathRev) FROM nodes WHERE nodeId == \"' + str(pre_node_id) + '\"')
            (prePathRev,) = cursor.fetchone()
        else:
            #find the nodeId and pathRev for the pre_node_name
            cursor = self.dbCursor.execute('SELECT nodeId, pathRev, lastPathRev FROM nodes WHERE name == \"' + pre_node_name + '\"')
            preNodeId, prePathRev = -1, -1
            while True:
                # bug: does not handle two entries with the same name, but different nodeIds
                data = cursor.fetchone()
                if data == None:
                    break
                (tmpPreNodeId, tmpPrePathRev, lastPathRev) = data
                if lastPathRev:
                    continue
                if tmpPrePathRev > prePathRev:
                    # get the latest revision of pre_node_name
                    preNodeId, prePathRev = tmpPreNodeId, tmpPrePathRev
                    
        # set the category id, either by using and exsisting id (add new nodes to the category) or creating a new category
        if category_name == None and category_id == None:
            categoryId = None
        elif category_id != None:
            # do not create a new category, instead add new nodes to an existing category
            categoryId = category_id
        elif category_name != None:
            # make a new category
            cursor = self.dbCursor.execute('SELECT MAX(categoryId) FROM categories')
            (categoryId,) = cursor.fetchone()
            categoryId += 1
            if show: print('  added new category: (categoryId, preCatId, category_name)', (categoryId, preNodeId, category_name))
            self.dbCursor.execute(self.sqlAdds['categories'], (categoryId, preNodeId, category_name))

        # add the nodes to both the nodes table and the preNodes table
        dx, dy = 1, 0
        for node in nodes:
            self.dbCursor.execute(self.sqlAdds['nodes'], (nodeId, pathRev, node, dx, dy, lastPathRev))
            self.dbCursor.execute(self.sqlAdds['preNodes'], (nodeId, pathRev, preNodeId, prePathRev, categoryId, None, None))
            if show:
                print('    added to nodes:', (nodeId, pathRev, node, dx, dy, lastPathRev))
                print('    added to preNodes:', (nodeId, pathRev, preNodeId, prePathRev, categoryId, None, None))
                
            nodeId += 1
            dy += 1
        self.db.commit()

    def dumpTable(self, table_name):
        dataTuples = []
        cursor = self.dbCursor.execute(self.sqlDumps[table_name])
        while True:
            dataTuple = cursor.fetchone()
            if dataTuple:
                dataTuples.append(dataTuple)
            else:
                break
        return tuple(dataTuples)

    def getNodeIds(self, name):
        cursor = self.dbCursor.execute('SELECT nodeId FROM nodes where name == \"' + name + '\"')
        nodeIds = []
        while True:
            data = cursor.fetchone()
            if data:
                (nodeId,) = data
                nodeIds.append(nodeId)
            else:
                break
        return tuple(nodeIds)
    
    def _addTable(self, table_name):
        show = False
        columnSpec = self.columnSpecs[table_name]
        if show: print('  columnSpec', columnSpec)
        self.db.execute('CREATE TABLE ' + table_name + ' (' + columnSpec + ')')
        self.dbCursor.execute(self.sqlAdds[table_name], self.tableInits[table_name])
        self.db.commit()

    def addNotes(self, table_name, notes):
        '''
        add new notes to the database
        '''
        show = True
        self.lock.acquire()

        # add the table if necessary
        try:
            self.dbCursor.execute('select MAX(id) FROM ' + table_name)
        except sqlite3.OperationalError:
            self.addTable(table_name)

        # add the data to the table
        additions = []
        numColumns = len(notes[0])
        #sqlAdd = 'INSERT INTO ' + table_name + '(noteText, date, user) VALUES ( ' + '?, ' * numColumns + ')'
        sqlAdd = 'INSERT INTO ' + table_name + '(noteText, date, owner) VALUES (?, ?, ?)'
        
        for i in range(len(notes)):
            (noteText, date, owner) = notes[i]
            try:
                additions.append((
                    str(noteText),
                    str(date),
                    str(owner))
                 )
            except:
                print('  ERROR in add note for note', notes[i])
        if show: print('  adding to database.  sql:', sqlAdd, '\n  additions:', additions)
        #for addition in additions:
        #    self.dbCursor.execute(sqlAdd, addition)
        self.dbCursor.executemany(sqlAdd, additions)
        self.db.commit()
        self.lock.release()
        return True

    def modifyNotes(self, table_name, notes):
        '''
        modify existing notes already in the database
        '''
        self.lock.acquire()

        # add the table if necessary
        try:
            self.dbCursor.execute('select MAX(id) FROM ' + table_name)
        except sqlite3.OperationalError:
            self.addTable(table_name)

        # modify data in the table
        changes = []
        sqlChange = 'UPDATE ' + table_name + ' SET noteText = ?, date = ?, owner = ?'
        for i in range(len(notes)):
            (noteText, date, owner) = notes[i]
            try:
                addition.append(
                    str(noteText),
                    str(date),
                    str(owner),
                 )
            except:
                print('  ERROR in add note for note', notes[i])
        if show: print('  making changes to the database')
        self.dbCursor.executemany(sqlChange, additions)
        self.db.commit()
        self.lock.release()
        return True
        
    def getNote(self, table_name, row_id):
        show = False
        cursor = self.dbCursor.execute('SELECT noteText, date, owner FROM ' + table_name + ' WHERE id == ' + str(row_id))
        (noteText, date, owner) = cursor.fetchone()
        if show: print('  for row', row_id, 'got', (noteText, date, owner))
        return (noteText, date, owner)
    
    def findNotes(self, table_name):
        pass

class AmbiguousNameException(BaseException): pass

if __name__ == '__main__':
#    path = '/home/stuart/code/button-grid/button-grid/database/test.db'
    path = './test.db'
    lock = multiprocessing.Lock()
    db = DatabaseInterface(path, lock)
    now = time.time()
    nowStr1 = time.ctime(now)
    time.sleep(1)
    now = time.time()
    nowStr2 = time.ctime(now)
    
    print(nowStr1, nowStr2)
    db.addNotes('newIdeas', (
        ('this is note 1', nowStr1, 'stuart'),
        ('this is note 2', nowStr2, 'stuart')))
                
    (noteText, date, owner) = db.getNote('newIdeas', 1)
    print('note id 1:', (noteText, date, owner))