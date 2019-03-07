#!/usr/bin/python3
'''
history:
2/3 - 
12/19 - eliminate tableInits?
12/19/18 - need to change categoryTable:preNodeId to preCatId
'''

import sqlite3
import multiprocessing
import time
from collections import OrderedDict

class CategorizerData:
    '''
    Reads and writes data to a set of tables which keep track of:
      notes and their categories
      relationships between the categories in which notes are taken.
      historical versions of both notes and categories

    Concepts:
      category (cat): A grouping in which notes can be placed with a semantic meaning which all the notes at least partially match.
      catVariant: A variant of a category.  The variation can be semantic of syntactic.  The variant has a different name than the category, though usually a similar name.  e.g. Given category 'Horse', a category variant could be 'equus'.
      relation (rel): A relationship between categories.  e.g. 'is-a', 'has-a'
      relVariant: A variant of a relation.  e.g. 'are', 'sub-component'
      catNode: A catNode 'is-a' catVariant.  A catNode is the category for zero or more notes.  Two catNodes can have identical categories and be different in their connections.
      catConnection: A connection 'is-a' relationVariant.  It connects two catNodes.
      pathRev: A pathRev identifies a set of catNodes and catConnections (path) at a specific time.  If changes have been made to the catNodes or catConnections, when a note is taken, the pathRev will be 'closed'.  Next time a change is made to the path, a new pathRev will be used.  This enables old notes to use old paths, eliminating the need to update all notes when a change is made to the path.

    schema:
      categories     : catId INTEGER, pathRev INTEGER, catName BLOB, validForLatest INTEGER, PRIMARY KEY (catId, pathRev)
      catVariants    : catVarId INTEGER, pathRev INTEGER, catId INTEGER, catVarName BLOB, validForLatest INTEGER, PRIMARY KEY (catVarId, pathRev)
      catNodes       : catNodeId INTEGER, pathRev INTEGER, catVarId INTEGER, dx INTEGER, dy INTEGER, validForLatest INTEGER, PRIMARY KEY (catNodeID, pathRev)
      relations      : relId INTEGER, pathRev INTEGER, prefix BLOB, relName BLOB, validForLatest INTEGER, PRIMARY KEY (relId, pathRev)
      relVariants    : relVarId INTEGER, pathRev INTEGER, relId INTEGER, relVarName BLOB, validForLatest INTEGER, PRIMARY KEY (relVarId, pathRev)
      catConnections : catNodeId INTEGER, pathRev INTEGER, relVarId INTEGER, superCatNodeId INTEGER, validForLatest INTEGER, PRIMARY KEY (catNodeId, pathRev, relVarId, superCatNodeId)
      pathRevs       : pathRev INTEGER, startDateTime BLOB, openForChange INTEGER, PRIMARY KEY (pathRev)

    '''
    def __init__(self, database_path_and_file_name, lock, in_memory = False, create_new_database = False):
        show = False
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
            'categories'   : 'catId INTEGER, pathRev INTEGER, catName BLOB, validForLatest INTEGER, PRIMARY KEY (catId, pathRev)',
            'catVariants'   : 'catVarId INTEGER, pathRev INTEGER, catId INTEGER, catVarName BLOB, validForLatest INTEGER, PRIMARY KEY (catVarId, pathRev)',
            'catNodes': 'catNodeId INTEGER, pathRev INTEGER, catVarId INTEGER, dx INTEGER, dy INTEGER, validForLatest INTEGER, PRIMARY KEY (catNodeID, pathRev)',
            'relations'   : 'relId INTEGER, pathRev INTEGER, prefix BLOB, relName BLOB, validForLatest INTEGER, PRIMARY KEY (relId, pathRev)',
            'relVariants'   : 'relVarId INTEGER, pathRev INTEGER, relId INTEGER, relVarName BLOB, validForLatest INTEGER, PRIMARY KEY (relVarId, pathRev)',
            'catConnections' : 'catNodeId INTEGER, pathRev INTEGER, relVarId INTEGER, superCatNodeId INTEGER, validForLatest INTEGER, PRIMARY KEY (catNodeId, pathRev, relVarId, superCatNodeId)',
            'pathRevs': 'pathRev INTEGER, startDateTime BLOB, openForChange INTEGER, PRIMARY KEY (pathRev)',
        #    'newIdeas': 'id INTEGER PRIMARY KEY AUTOINCREMENT, noteText BLOB, date BLOB, owner BLOB',
        #    'toDo'    : 'id INTEGER PRIMARY KEY AUTOINCREMENT, noteText BLOB, date BLOB, owner BLOB, completeByDate BLOB'
        }

        self.sqlAdds = {
            'categories'   : 'INSERT INTO categories (catId, pathRev, catName, validForLatest) VALUES (?, ?, ?, ?)',
            'catVariants' : 'INSERT INTO catVariants (catVarId, pathRev, catId, catVarName, validForLatest) VALUES (?, ?, ?, ?, ?)',
            'catNodes': 'INSERT INTO catNodes (catNodeId, pathRev, catVarId, dx, dy, validForLatest) VALUES (?, ?, ?, ?, ?, ?)',
            'relations' : 'INSERT INTO relations (relID, pathRev, prefix, relName, validForLatest) VALUES (?, ?, ?, ?, ?)',
            'relVariants' : 'INSERT INTO relVariants (relVarID, pathRev, relId, relVarName, validForLatest) VALUES (?, ?, ?, ?, ?)',
            'catConnections' : 'INSERT INTO catConnections (catNodeId, pathRev, relVarId, superCatNodeId, validForLatest) VALUES (?, ?, ?, ?, ?)',
            'pathRevs': 'INSERT INTO pathRevs (pathRev, startDateTime, openForChange) VALUES (?, ?, ?)',
        }

        self.sqlDumps = {
            'categories' : 'SELECT catId, pathRev, catName, validForLatest from categories',
            'catVariants' : 'SELECT catVarId, pathRev, catId, catVarName, validForLatest from catVariants',
            'catNodes' : 'SELECT catNodeId, pathRev, catVarId, dx, dy, validForLatest from catNodes',
            'relations' : 'SELECT relID, pathRev, prefix, relName, validForLatest from relations',
            'relVariants' : 'SELECT relVarID, pathRev, relId, relVarName, validForLatest from relVariants',
            'catConnections' : 'SELECT catNodeId, pathRev, relVarId, superCatNodeId, validForLatest from catConnections',
            'pathRevs': 'SELECT pathRev, startDateTime, open from pathRevs',
        }

        
        self.tableInits = {
            'categories'   : (0, 0, None, 0),
            'catVariants'   : (0, 0, 0, None, 0),
            'catNodes'   : (0, 0, 0, None, None, 0),
            'relations'  : (0, 0, None, None, 0),
            'relVariants'  : (0, 0, 0, None, 0),
            'catConnections' : (0, 0, 0, None, 0),
            'pathRevs': (1, int(time.time()), 1),
        }

        # create a lists of column names
        self.catsColumnNames = []
        self.catVarsColumnNames = []
        self.pathRevColumnNames = []
        self.catNodesColumnNames = []

        if show: print('  creating column names for table categories:')
        catsColumnSpec = self.columnSpecs['categories']
        names = catsColumnSpec.split()
        for i in range(0, len(names) - 4, 2):
            self.catsColumnNames.append(names[i])
            if show: print('   ', names[i])#, name.replace(',','') )

        if show: print('  creating column names for table catVariants:')
        catVarsColumnSpec = self.columnSpecs['catVariants']
        names = catVarsColumnSpec.split()
        for i in range(0, len(names) - 4, 2):
            self.catVarsColumnNames.append(names[i])
            if show: print('   ', names[i])#, name.replace(',','') )

        if show: print('  creating column names for table catNodes:')
        catNodesColumnSpec = self.columnSpecs['catNodes']
        names = catNodesColumnSpec.split()
        for i in range(0, len(names) - 4, 2):
            self.catNodesColumnNames.append(names[i])
            if show: print('   ', names[i])#, name.replace(',','') )

        self.pathRevsColumnNames = []
        nodesColumnSpec = self.columnSpecs['pathRevs']
        names = nodesColumnSpec.split()
        if show: print('  creating column names for table pathRevs:')
        for i in range(0, len(names) - 4, 2):
            self.pathRevsColumnNames.append(names[i])
            if show: print('   ', names[i])#, name.replace(',','') )

        if create_new_database:
            for tableName in self.columnSpecs.keys():
                if show: print('    tableName', tableName)
                columnSpec = self.columnSpecs[tableName]
                entries = columnSpec.split()
                idName = entries[0]
                try:
                    self.dbCursor.execute('select MAX(' + idName + ') FROM ' + tableName)
                    assert False, 'I was asked to create a new database, but there is already a database with something in it'
                except sqlite3.OperationalError:
                    self._addTable(tableName)

    def _OLDgetNodeInfo(self, node_name):
        '''
        returns all instances of node_name both for standard name and aliases. 
        if node_name exists:
          return (
                  (nodeIdA, nodeName, categoryId1, categoryName1, alias1, preNodeId1, preNodeName1), 
                  (nodeIdA, nodeName, categoryId2, categoryName2, alias2, preNodeId2, preNodeName2),
                  (nodeIdB, nodeName, categoryId3, categoryName3, alias3, preNodeId3, preNodeName3),
                  ... ,
                 )
        else:
          return ()
        '''

        # get the data from 'categories' for this node name
        nodesData = []
        cursor = self.dbCursor.execute(r'SELECT nodeId FROM nodes WHERE name == "' + node_name + '" AND validForLatest > 0')
        while True:
            data = cursor.fetchone()
            if not data:
                break
            (nodeId, ) = data
            nodesData.append( (nodeId, node_name) )

        # the node_name could be an alias, so get the data from preNodes
        preNodesData = []
        cursor = self.dbCursor.execute(r'SELECT nodeId FROM preNodes WHERE nameAlias == "' + node_name + '" AND validForLatest > 0')
        while True:
            data = cursor.fetchone()
            if not data:
                break
            
            (nodeId, ) = data
            preNodesData.append(nodeId)

        # get the preNodes names
        for preNodeId in preNodesData:
            cursor = self.dbCursor.execute(r'SELECT name FROM nodes WHERE nodeId == ' + str(preNodeId) + ' AND validForLatest > 0')
            (name,) = cursor.fetchone()
            nodesData.append( (preNodeId, name) )
        
        # get data from preNodes table
        retData = []
        for (nodeId, name) in nodesData:
            cursor = self.dbCursor.execute(r'SELECT preNodeId, categoryId, nameAlias from preNodes WHERE nodeId == ' + str(nodeId) + ' AND validForLatest > 0')
            while True:
                data = cursor.fetchone()
                if not data:
                    break
                (preNodeId, categoryId, nameAlias) = data
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

    def _getPathRev(self):
        # get the pathRev
        cursor = self.dbCursor.execute('SELECT MAX(' + self.pathRevsColumnNames[0] + ') FROM pathRevs')
        (pathRev,) = cursor.fetchone()
        cursor = self.dbCursor.execute('SELECT ' + self.pathRevsColumnNames[2] + ' FROM pathRevs')
        (openForChange,) = cursor.fetchone()
        if openForChange:
            pass
        else:
            # make a new pathRev, add it to pathRevs and mark it open
            pathRev += 1
            self.dbCursor.execute(self.sqlAdds['pathRevs'], (pathRev, int(time.time()), 1))
        return pathRev
    
#    def addPathRev(self):
#        self.dbCursor.execute(self.sqlAdds['categories'], (categoryId, preNodeId, category_name))

    def addCatNode(self, cat_var_id = None, cat_var_name = None):
        '''
        Add a single new catNode with no connections.
        Must have either cat_var_id or cat_var_name.
        If cat_var_id is provided, will add a catNode with that catVarId.
        If cat_var_name is provided, add a new category, catVariant, then add a catNode with the new catVarId.
        '''
        if cat_var_id:
            catNodeId = self._addCatNode(cat_var_id)
        elif cat_var_name:
            catVarId = self._addCategory(cat_var_name) #adds category and catVariant and returns catVarId
            catNodeId = self._addCatNode(catVarId)
        else:
            print('ERROR must provide either cat_var_id or cat_var_name')
            assert False
        return catNodeId

    def _addCatNode(self, cat_var_id):
        show = False
        if show: print('in _addCatNode() with cat_var_id', cat_var_id)        

        pathRev = self._getPathRev()

        # get the next catId
        cursor = self.dbCursor.execute('SELECT MAX(' + self.catNodesColumnNames[0] + ') FROM catNodes')
        (catNodeId,) = cursor.fetchone()
        catNodeId += 1
        if show: print('  catNodeId', catNodeId, ', pathRev', pathRev)

        self.dbCursor.execute(self.sqlAdds['catNodes'], (catNodeId, pathRev, cat_var_id, None, None, 1))
        if show:
            print('    added new catNode:', (catNodeId, pathRev, cat_var_id, None, None, 1))
        return catNodeId
    

    def _addCategory(self, cat_name):
        '''
        Add a single category.  This is called when user is adding nodes.  If the category for the node does not 
        exist, this will be detected and the category automatically added.
        The category must be added before it is used for a node.
        '''
        show = False
        if show: print('in _addCategory() with cat_name', cat_name)        

        pathRev = self._getPathRev()

        # get the next catId
        cursor = self.dbCursor.execute('SELECT MAX(' + self.catsColumnNames[0] + ') FROM categories')
        (catId,) = cursor.fetchone()
        catId += 1
        if show: print('  catId', catId, ', pathRev', pathRev)

        self.dbCursor.execute(self.sqlAdds['categories'], (catId, pathRev, cat_name, 1))
        if show:
            print('    added new category:', (catId, pathRev, cat_name, 1))

        # add the default catVariant for the category
        cursor = self.dbCursor.execute('SELECT MAX(' + self.catVarsColumnNames[0] + ') FROM catVariants')
        (catVarId,) = cursor.fetchone()
        catVarId += 1        
        self.dbCursor.execute(self.sqlAdds['catVariants'], (catVarId, pathRev, catId, None, 1))
        
        self.db.commit()
        return catVarId
    
    def _addCatVariant(self, cat_id, cat_var_name):
        '''
        Add a single category variant.  This is called when user is adding nodes.  If a category is selected
        but the user providee a name different than the category name, the category variant will be
        automatically added.
        The category and at least the default category variant must be added before it is used for a node.
        '''
        show = True
        if show: print('in _addCatVariant() with cat_id', cat_id, ', cat_var_name', cat_var_name)        

        pathRev = self._getPathRev()

        # add the catVariant for the category
        cursor = self.dbCursor.execute('SELECT MAX(' + self.catVarsColumnNames[0] + ') FROM catVariants')
        (catVarId,) = cursor.fetchone()
        catVarId += 1        
        self.dbCursor.execute(self.sqlAdds['catVariants'], (catVarId, pathRev, cat_id, cat_var_name, 1))
        
        self.db.commit()
        return catVarId
    
    def editCatNode(self, node_id, name = None, dx = None, dy = None):
        '''
        Given a node_id selected from the GUI, change one or more of name, dx, dy
        '''
        pass
    
#    def editPreNode(self, node_id, pre_node_id_orig, pre_node_id_new = None, category_id_orig = None, category_id_new = None, name_alias = None, dx = None, dy = None):
#        '''
#        edit one of the connections from the node to a pre_node
#        pre_node_id and category_id are primary keys, so to change them, it is necessary to provide the originals as well as the new ids.
#        '''
#        pass
    
#    def addNodesToCategory(self, nodes, category_name = None, category_id = None, pre_node_name = None, pre_node_id = None):
#        '''
#        OBSOLETE
#        do not create a new category, reuse an existing category, just extend it with new nodes
#        calls addNodes with category_id specified.
#        '''
#        # get the category id and pass it to addNodes which will know to add to the category since it got the category id
#        if category_id != None:
#            categoryId = category_id
#        else:
#            cursor = self.dbCursor.execute('SELECT categoryID FROM categories WHERE catName == \"' + str(category_name) + '\"')
#            data = cursor.fetchone()
#            if data:
#                (categoryId,) = data
#            else:
#                return False
#            data2 = cursor.fetchone()
#            if data2:
#                # there are two different categories with the same name.  The user will need to figure out which one he wants
#                raise AmbiguousNameException()
#        self.addNodes(nodes, category_name, categoryId, pre_node_name, pre_node_id)
        
#    def addNodes(self, nodes, category_name = None, category_id = None, pre_node_name = None, pre_node_id = None):
#        '''
#        OBSOLETE
#        add the nodes to the table nodes, add information to preNodes, and if the category is new, add a new category
#        nodes: a list of nodes to be added to the nodes table and the preNodes table
#        category: the category for the preNodes table
#        pre_node_name, pre_node_id:
#          None, None: No preNode is specified, which is OK, just leave preNode data blank
#          'name', None: a name is specified, but no nodeId, so look up the nodeId corresponding to the name
#          None, nodeId: the nodeId is specified, so use that directly
#          'name', nodeId: both are specified, validate the name matches the nodeId
#        raises AmbiguousNameException if the category_name or pre_node_name is given without its corresponding id, and there are more than one id with the same name.
#        '''
#        show = False
#        if show: print('in addNodes() with nodes', nodes, ', category_name', category_name, ', category_id', category_id, ', pre_node_name', pre_node_name, ', pre_node_id', pre_node_id)
#
#        # get the max nodeId and pathRev so we can add new nodes with unique ids and assign them a new pathRev
#        nodesColumnSpec = self.columnSpecs['nodes']
#        entries = nodesColumnSpec.split()
#        nodesPrimaryKey1 = entries[-2].replace('(','').replace(',','')
#        nodesPrimaryKey2 = entries[-1].replace(')','').replace(',','')
#        if show: print('  nodes table primary keys:', nodesPrimaryKey1, nodesPrimaryKey2)
#        cursor = self.dbCursor.execute('SELECT MAX(' + nodesPrimaryKey1 + ') FROM nodes')
#        (nodeId,) = cursor.fetchone()
#        nodeId += 1
#        cursor = self.dbCursor.execute('SELECT MAX(' + nodesPrimaryKey2 + ') FROM nodes')
#        (pathRev,) = cursor.fetchone()
#        pathRev += 1
#            
#        # find the preNodeId if possible or raise an AmbiguousNameException
#        lastPathRev = None
#        if pre_node_name == None and pre_node_id == None:
#            preNodeId = None
#            prePathRev = None
#        elif pre_node_id != None:
#            preNodeId = pre_node_id
#            cursor = self.dbCursor.execute('SELECT MAX(pathRev) FROM nodes WHERE nodeId == \"' + str(pre_node_id) + '\"')
#            (prePathRev,) = cursor.fetchone()
#        else:
#            #find the nodeId and pathRev for the pre_node_name
##            cursor = self.dbCursor.execute('SELECT nodeId, pathRev, lastPathRev FROM nodes WHERE name == \"' + pre_node_name + '\"')
#            cursor = self.dbCursor.execute('SELECT nodeId, pathRev FROM nodes WHERE name == \"' + pre_node_name + '\" AND validForLatest > 0')
#            preNodeId, prePathRev = -1, -1
##            while True:
##                # bug: does not handle two entries with the same name, but different nodeIds
#            data = cursor.fetchone()
##                if data == None:
##                    break
##                (tmpPreNodeId, tmpPrePathRev, lastPathRev) = data
#            (preNodeId, prePathRev) = data
##                if lastPathRev:
##                    continue
##                if tmpPrePathRev > prePathRev:
##                    # get the latest revision of pre_node_name
##                    preNodeId, prePathRev = tmpPreNodeId, tmpPrePathRev
#                    
#        # set the category id, either by using and exsisting id (add new nodes to the category) or creating a new category
#        if category_name == None and category_id == None:
#            categoryId = None
#        elif category_id != None:
#            # do not create a new category, instead add new nodes to an existing category
#            categoryId = category_id
#        elif category_name != None:
#            # make a new category
#            cursor = self.dbCursor.execute('SELECT MAX(categoryId) FROM categories')
#            (categoryId,) = cursor.fetchone()
#            categoryId += 1
#            if show: print('  added new category: (categoryId, preCatId, category_name)', (categoryId, preNodeId, category_name))
#            self.dbCursor.execute(self.sqlAdds['categories'], (categoryId, preNodeId, category_name))
#
#        # add the nodes to both the nodes table and the preNodes table
#        dx, dy = 1, 0
#        for node in nodes:
##            self.dbCursor.execute(self.sqlAdds['nodes'], (nodeId, pathRev, node, dx, dy, lastPathRev))
#            self.dbCursor.execute(self.sqlAdds['nodes'], (nodeId, pathRev, node, dx, dy, 1))
##            self.dbCursor.execute(self.sqlAdds['preNodes'], (nodeId, pathRev, preNodeId, prePathRev, categoryId, None, None))
#            self.dbCursor.execute(self.sqlAdds['preNodes'], (nodeId, pathRev, preNodeId, prePathRev, categoryId, None, 1))
#            if show:
##                print('    added to nodes:', (nodeId, pathRev, node, dx, dy, lastPathRev))
#                print('    added to nodes:', (nodeId, pathRev, node, dx, dy, 1))
##                print('    added to preNodes:', (nodeId, pathRev, preNodeId, prePathRev, categoryId, None, None))
#                print('    added to preNodes:', (nodeId, pathRev, preNodeId, prePathRev, categoryId, None, 1))
#                
#            nodeId += 1
#            dy += 1
#        self.db.commit()

    def dumpTable(self, table_name):
        '''
        returns all of the data in a table as a list of tuples
        '''
        dataTuples = []
        cursor = self.dbCursor.execute(self.sqlDumps[table_name])
        while True:
            dataTuple = cursor.fetchone()
            if dataTuple:
                dataTuples.append(dataTuple)
            else:
                break
        return tuple(dataTuples)

#    def getNodeIds(self, name):
#        cursor = self.dbCursor.execute('SELECT nodeId FROM nodes where name == \"' + name + '\"')
#        nodeIds = []
#        while True:
#            data = cursor.fetchone()
#            if data:
#                (nodeId,) = data
#                nodeIds.append(nodeId)
#            else:
#                break
#        return tuple(nodeIds)
    
    def _addTable(self, table_name):
        show = False
        if show: print('in _addTable() with table_name', table_name)
        columnSpec = self.columnSpecs[table_name]
        if show: print('  columnSpec', columnSpec)
        self.db.execute('CREATE TABLE ' + table_name + ' (' + columnSpec + ')')
        self.dbCursor.execute(self.sqlAdds[table_name], self.tableInits[table_name])
        self.db.commit()

    def addNotes(self, table_name, notes):
        '''
        NOT IMPLEMENTED YET
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
        NOT IMPLEMENTED
        modify existing notes already in the database
        not implemented
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
        '''
        not implemented
        '''
        show = False
        cursor = self.dbCursor.execute('SELECT noteText, date, owner FROM ' + table_name + ' WHERE id == ' + str(row_id))
        (noteText, date, owner) = cursor.fetchone()
        if show: print('  for row', row_id, 'got', (noteText, date, owner))
        return (noteText, date, owner)
    
    def findNotes(self, table_name):
        '''
        not implemented
        '''
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
