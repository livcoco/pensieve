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
      relations      : relId INTEGER, pathRev INTEGER, relPrefix BLOB, relName BLOB, validForLatest INTEGER, PRIMARY KEY (relId, pathRev)
      relVariants    : relVarId INTEGER, pathRev INTEGER, relId INTEGER, relVarName BLOB, validForLatest INTEGER, PRIMARY KEY (relVarId, pathRev)
      catConnections : catNodeId INTEGER, pathRev INTEGER, relVarId INTEGER, superCatNodeId INTEGER, validForLatest INTEGER, PRIMARY KEY (catNodeId, pathRev, relVarId, superCatNodeId)
      pathRevs       : pathRev INTEGER, startDateTime BLOB, openForChange INTEGER, PRIMARY KEY (pathRev)

    for a more complete picture:
    ../../../IHMC\ CmapTools/CmapTools &
    open pensieve_database_schema

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
            'relations'   : 'relId INTEGER, pathRev INTEGER, relPrefix BLOB, relName BLOB, direction BLOB, validForLatest INTEGER, PRIMARY KEY (relId, pathRev)',
            'relVariants'   : 'relVarId INTEGER, pathRev INTEGER, relId INTEGER, relVarPrefix BLOB, relVarName BLOB, varDirection BLOB, validForLatest INTEGER, PRIMARY KEY (relVarId, pathRev)',
            'catConnections' : 'catNodeId INTEGER, pathRev INTEGER, relVarId INTEGER, superCatNodeId INTEGER, validForLatest INTEGER, PRIMARY KEY (catNodeId, pathRev, relVarId, superCatNodeId)',
            'pathRevs': 'pathRev INTEGER, startDateTime BLOB, openForChange INTEGER, PRIMARY KEY (pathRev)',
        #    'newIdeas': 'id INTEGER PRIMARY KEY AUTOINCREMENT, noteText BLOB, date BLOB, owner BLOB',
        #    'toDo'    : 'id INTEGER PRIMARY KEY AUTOINCREMENT, noteText BLOB, date BLOB, owner BLOB, completeByDate BLOB'
        }

        self.sqlAdds = {
            'categories'   : 'INSERT INTO categories (catId, pathRev, catName, validForLatest) VALUES (?, ?, ?, ?)',
            'catVariants' : 'INSERT INTO catVariants (catVarId, pathRev, catId, catVarName, validForLatest) VALUES (?, ?, ?, ?, ?)',
            'catNodes': 'INSERT INTO catNodes (catNodeId, pathRev, catVarId, dx, dy, validForLatest) VALUES (?, ?, ?, ?, ?, ?)',
            'relations' : 'INSERT INTO relations (relID, pathRev, relPrefix, relName, direction, validForLatest) VALUES (?, ?, ?, ?, ?, ?)',
            'relVariants' : 'INSERT INTO relVariants (relVarID, pathRev, relId, relVarPrefix, relVarName, varDirection, validForLatest) VALUES (?, ?, ?, ?, ?, ?, ?)',
            'catConnections' : 'INSERT INTO catConnections (catNodeId, pathRev, relVarId, superCatNodeId, validForLatest) VALUES (?, ?, ?, ?, ?)',
            'pathRevs': 'INSERT INTO pathRevs (pathRev, startDateTime, openForChange) VALUES (?, ?, ?)',
        }

        self.sqlDumps = {
            'categories' : 'SELECT catId, pathRev, catName, validForLatest from categories',
            'catVariants' : 'SELECT catVarId, pathRev, catId, catVarName, validForLatest from catVariants',
            'catNodes' : 'SELECT catNodeId, pathRev, catVarId, dx, dy, validForLatest from catNodes',
            'relations' : 'SELECT relID, pathRev, relPrefix, relName, direction, validForLatest from relations',
            'relVariants' : 'SELECT relVarID, pathRev, relId, relVarPrefix, relVarName, varDirection, validForLatest from relVariants',
            'catConnections' : 'SELECT catNodeId, pathRev, relVarId, superCatNodeId, validForLatest from catConnections',
            'pathRevs': 'SELECT pathRev, startDateTime, open from pathRevs',
        }

        
        self.tableInits = {
            'categories'   : (0, 0, None, 0),
            'catVariants'   : (0, 0, 0, None, 0),
            'catNodes'   : (0, 0, 0, None, None, 0),
            'relations'  : (0, 0, None, None, None, 0),
            'relVariants'  : (0, 0, 0, None, None, None, 0),
            'catConnections' : (0, 0, 0, None, 0),
            'pathRevs': (1, int(time.time()), 1),
        }

        # create a lists of column names
        self.catsColumnNames = []
        self.catVarsColumnNames = []
        self.pathRevColumnNames = []
        self.catNodesColumnNames = []
        self.relsColumnNames = []
        self.relVarsColumnNames = []
        
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

        if show: print('  creating column names for table relations:')
        relsColumnSpec = self.columnSpecs['relations']
        names = relsColumnSpec.split()
        for i in range(0, len(names) - 4, 2):
            self.relsColumnNames.append(names[i])
            if show: print('   ', names[i])

        if show: print('  creating column names for table relVariants:')
        relVarsColumnSpec = self.columnSpecs['relVariants']
        names = relVarsColumnSpec.split()
        for i in range(0, len(names) - 4, 2):
            self.relVarsColumnNames.append(names[i])
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
            if show: print('  creating new database')
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
    
    def addCatNode(self, cat_var_id = None, cat_var_name = None):
        '''
        Add a single new catNode with no connections.
        Must have either cat_var_id or cat_var_name.
        If cat_var_id is provided, will add a catNode with that catVarId.
        If cat_var_name is provided, add a new category, catVariant, then add a catNode with the new catVarId.
        The application code should find the cat_var_id before calling this method.  If it cannot find it, then call this method with a cat_var_name, and a new category and category variant will be created.
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

    def addConnection(self, cat_node_id, super_cat_node_id, rel_var_id = None, rel_var_name = None):
        '''
        add a connection between two cat nodes.
        if rel_var_id is specified, use it for the relation and ignore rel_var_name
        if rel_var_id is not specified and rel_var_name is specified, look for the relation variant with that name.
          if the relation variant is not found, make a new relation and relation variant
          if the relation variant is found, get the relVarId and use it
        if neither rel_var_id or rel_var_name is specified, use relation variant id 0.
        '''
        show = False
        if show: print('in addConnection() with cat_node_id', cat_node_id, ', super_cat_node_id', super_cat_node_id, ', rel_var_id', rel_var_id, ', rel_var_name', rel_var_name)
        pathRev = self._getPathRev()
        if rel_var_id == None:
            if rel_var_name == None:
                rel_var_id = 0
            else:
                rel_var_id = self._getRelVarId(rel_var_name)
            
        self.dbCursor.execute(self.sqlAdds['catConnections'], (cat_node_id, pathRev, rel_var_id, super_cat_node_id, 1))
        self.db.commit()
        
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

    def _getRelVarId(self, rel_var_name):
        '''
        given a relation variant name, find the correct relation Variant Id (relVarId)
        if the rel_var_name exists in the relationVariants table:
          return the relVarId of the first instance of the name.  
          More than one instance of the name can exist in the table, if so, 
            the user can fix it later by providing the correct relVarId.
        if the rel_var_name does not exist in the relationVariants table:
          look for the name in the relations table.
          if the name exists in the relations table, use the first instance of the name
            return the relVarId of the default relation variant for the relation (relVarName = None)
            More than one instance of the name can exist in the table, if so, 
              the user can fix it later by providing the correct relVarId.
          if the name does not exist, 
            create a new relation and a new default relation variant and return the new relVarId
        '''
        show = False
        if show: print('in _getRelVarId() with rel_var_name', rel_var_name)
        sql = 'SELECT ' + self.relVarsColumnNames[0] + ' FROM relVariants WHERE ' + self.relVarsColumnNames[4] + ' = "' + rel_var_name + '"'
        if show: print('  sql', sql)
        cursor = self.dbCursor.execute(sql)
        data = cursor.fetchone()
        if data:
            #found an exact match of the name
            (relVarId,) = data
        else:
            sql = 'SELECT ' + self.relsColumnNames[0] + ' FROM relations WHERE ' + self.relsColumnNames[3] + ' = "' + rel_var_name + '"'
            if show: print('  sql', sql)
            cursor = self.dbCursor.execute(sql)
            data = cursor.fetchone()
            if data:
                # found an exact match of the name in the relations table
                (relId,) = data
                # find the default relVarId for this relation
                sql = 'SELECT ' + self.relVarsColumnNames[0] + ' FROM relVariants WHERE ' + self.relVarsColumnNames[2] + ' = ' + str(relId)# + ' AND ' + self.relVarsColumnNames[4] + ' = "' + str(None) + '"'
                if show: print('  sql', sql)
                cursor = self.dbCursor.execute(sql)
                (relVarId,) = cursor.fetchone()
            else:
                # did not find the relation name anywhere, create a new relation
                relVarId = self._addRelation(None, rel_var_name, None)
                
        if show: print('  returning relVarId', relVarId)
        return relVarId
    
    def _addCategory(self, cat_name):
        '''
        Add a single category.  This is called when user is adding nodes using addCatNode() and providing a category name and not a category id.  
        If the category for the node does not exist, this will be detected and the category automatically added.
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

        # add the category
        self.dbCursor.execute(self.sqlAdds['categories'], (catId, pathRev, cat_name, 1))
        if show:
            print('    added new category:', (catId, pathRev, cat_name, 1))

        # add the default catVariant for the category
        catVarId = self._addCatVariant(catId, None) # does self.db.commit()

        return catVarId
    
    def _addCatVariant(self, cat_id, cat_var_name):
        '''
        Add a single category variant.  This is called when user is adding nodes.  If a category is selected
        but the user providee a name different than the category name, the category variant will be
        automatically added.
        The category and at least the default category variant must be added before it is used for a node.
        '''
        show = False
        if show: print('in _addCatVariant() with cat_id', cat_id, ', cat_var_name', cat_var_name)

        pathRev = self._getPathRev()

        # add the catVariant for the category
        cursor = self.dbCursor.execute('SELECT MAX(' + self.catVarsColumnNames[0] + ') FROM catVariants')
        (catVarId,) = cursor.fetchone()
        catVarId += 1
        self.dbCursor.execute(self.sqlAdds['catVariants'], (catVarId, pathRev, cat_id, cat_var_name, 1))
        self.db.commit()
        return catVarId

    def _addRelation(self, rel_prefix, rel_name, direction):
        show = False
        if show: print('in _addRelation() with rel_prefix', rel_prefix, ', rel_name', rel_name, ', direction', direction)
        pathRev = self._getPathRev()

        # get the next relId
        cursor = self.dbCursor.execute('SELECT MAX(' + self.relsColumnNames[0] + ') FROM relations')
        (relId,) = cursor.fetchone()
        relId += 1
        if show: print('  relId', relId, ', pathRev', pathRev)

        self.dbCursor.execute(self.sqlAdds['relations'], (relId, pathRev, rel_prefix, rel_name, direction, 1))
        if show:
            print('    added new relation:', (relId, pathRev, rel_prefix, rel_name, direction, 1))

        # add the default relVariant for the category
        relVarId = self._addRelVariant(relId)

        return relVarId
        
    def _addRelVariant(self, rel_id, rel_var_prefix = None, rel_var_name = None, var_direction = None):
        '''
        Add a single relation variant.  This is called when user is adding nodes.  If a relation is selected but the user provides a prefix, name, or direction different than the relation prefix, name, or direction, the relation variant will be automatically added.
        The relation variant (could be the default relation variant) must be added before it is used for a node.
        '''
        show = False
        if show: print('in _addRelVariant() with rel_id', rel_id, ', rel_var_prefix', rel_var_prefix, ', rel_var_name', rel_var_name, ', var_direction', var_direction)        

        pathRev = self._getPathRev()

        # add the relVariant for the relation
        cursor = self.dbCursor.execute('SELECT MAX(' + self.relVarsColumnNames[0] + ') FROM relVariants')
        (relVarId,) = cursor.fetchone()
        relVarId += 1        
        self.dbCursor.execute(self.sqlAdds['relVariants'], (relVarId, pathRev, rel_id, rel_var_prefix, rel_var_name, var_direction, 1))
        
        self.db.commit()
        return relVarId

    def editCatNode(self, cat_node_id, cat_var_id = None, dx = None, dy = None):
        '''
        Given a cat_node_id selected from the GUI, change one of more of; category variant id, dx, dy
        the category variant must be created first, then the catVarId passed to this method.

        if the pathRev of the catNode is current:
          simply change the current catNode

        if the pathRev of the catNode is not current:
          create a new catNode with the new pathRev and catVarId, cloning the rest of the data.
          create new catConnections with the new catNodeId and pathRev, cloning the rest of the data.
          mark the old catNode validForLatest = False
          mark the old catConnections' validForLatest = False
        '''
        show = False
        if show: print('in editCatNode() with cat_node_id', cat_node_id, ', cat_var_id', cat_var_id, ', dx', dx, ', dy', dy)
        if cat_var_id == None and dx == None and dy == None:
            return

        # get the latest pathRev
        pathRev = self._getPathRev()

        # get the path rev of the latest version of this catNode and the corresponding sql WHERE statement
        (rowPathRev, sqlWhere) = self._getRowPathRevAndSQLWhere('catNodes', cat_node_id, self.catNodesColumnNames) 

        if rowPathRev == pathRev:
            # The pathRevs are the same, so we can just change the existing tuple with what we need to change
            if show: print('    rowPathRev == pathRev, updating data:')
            colValPairs = []
            if cat_var_id != None:
                colValPairs.append( (self.catNodesColumnNames[2], cat_var_id) )
            if dx != None:
                colValPairs.append( (self.catNodesColumnNames[3], dx) )
            if dy != None:
                colValPairs.append( (self.catNodesColumnNames[4], dy) )
            self._editRow('catNodes', colValPairs, sqlWhere)
        else:
            # The pathRevs are not the same, so we need to make a new tuple in the database
            if show: print('    rowPathRev != pathRev, marking existing row to not validForLatest and creating new row:')
            # get all the existing values from the current row
            (catNodeIdName, pathRevName, catVarIdName, dxName, dyName) = self.catNodesColumnNames[:5]
            sql = 'SELECT ({cni}, {pr}, {cvi}, {dx}, {dy} FROM catNodes '.format(cni=catNodeIdName, pr=pathRevName, cvi=catVarIdName, dx=dxName, dy=dyName) + sqlWhere
            cursor = self.dbCursor.execute(sql)
            (catNodeId, rowPathRev, oldCatVarId, oldDx, oldDy) = cursor.fetchone()

            # set validForLatest of the old one to 0
            columnName, value = self.catNodesColumnNames[5], 0
            sql = 'UPDATE catNodes SET {col} = {val}'.format(col = columnName, val = value) + sqlWhere
            if show: print('      updating validForLatest: sql = \"', sql, '\"')
            self.dbCursor.execute(sql)

            # create a new version of the catNode which is a new row in the table.  We change one of the primary keys: pathRev
            if cat_var_id == None:
                catVarId = oldCatVarId
            else:
                catVarId = cat_var_id
            if dx == None:
                dx = oldDx
            if dy == None:
                dy = oldDy
            self.dbCursor.execute(self.sqlAdds['catNodes'], (catNodeId, pathRev, catVarId, dx, dy, 1))
        self.db.commit()

    def _getRowPathRevAndSQLWhere(self, table_name, row_id, column_names):
        '''
        the 1st column of all tables must be an id
        the 2nd column of all tables must be pathRev
        the last column of all tables must be validForLatest
        '''
        show = False
        if show: print('in _getRowPathRevAndSQLWhere() with table_name', table_name, ', row_id', row_id, ', column_names', column_names)
        sqlWhere = ' WHERE ' + column_names[0] + ' == ' + str(row_id) + ' AND ' + column_names[-1] + ' == 1'
        sql = 'SELECT ' + column_names[1] + ' FROM ' + table_name + sqlWhere
        cursor = self.dbCursor.execute(sql)
        (rowPathRev,) = cursor.fetchone()
        if show: print('  returning (rowPathRev', rowPathRev, ', sqlWhere', sqlWhere, ')')
        return (rowPathRev, sqlWhere)
    
    def _editRow(self, table_name, column_value_pairs, sql_where):
        show = False
        if show: print('in _editRow() with table_name', table_name, ', column_value_pairs', column_value_pairs, ', sql_where', sql_where)
        sql = 'UPDATE catNodes SET'
        for (columnName, value) in column_value_pairs:
            sql += ' {col} = {val},'.format(col = columnName, val = value)
        sql = sql[:-1] + sql_where #get rid of the last comma and append the 'WHERE' statement
        if show: print('  updating row with sql = \"', sql, '\"')
        self.dbCursor.execute(sql)

    def moveCatNode(self, cat_node_id, dx = None, dy = None):
        '''
        provide a new location for the category node
        '''
        pass

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
