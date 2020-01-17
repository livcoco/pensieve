#!/usr/bin/python3
'''
history:
1/15/20 - use join() instead of += for strings? e.g. ', '.join( ('a','b','c') )  ... ', '.join(it[j] for j in range(0, len(it), 2))
          create fontSet namedtuple, as well as lineSet, headTypeSet and pass as arguments.
1/1/20 - added Double Metaphone (improvement on Soundex) to my system from https://pypi.org/project/Fuzzy/
11/6 - cleaned up editCatNode()
12/19 - eliminate tableInits?
12/19/18 - need to change categoryTable:preNodeId to preCatId
'''

import sqlite3
import multiprocessing
import time
from collections import OrderedDict
import fuzzy

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

    for a more complete picture:
    ../../../IHMC\ CmapTools/CmapTools &
    open pensieve_database_schema

    '''
    dMeta = fuzzy.DMetaphone()
    columnSpecs = {
        'categories'   : 'catId INTEGER, pathRev INTEGER, catName BLOB, dMetaName0 BLOB, dMetaName1 BLOB, validForLatest INTEGER, PRIMARY KEY (catId, pathRev)',
        'catVariants'   : 'catVarId INTEGER, pathRev INTEGER, catId INTEGER, catVarName BLOB, dMetaName0 BLOB, dMetaName1 BLOB, validForLatest INTEGER, PRIMARY KEY (catVarId, pathRev)',
        'catNodes': 'catNodeId INTEGER, pathRev INTEGER, catVarId INTEGER, dx INTEGER, dy INTEGER, dz INTEGER, nodeStyleId INTEGER, validForLatest INTEGER, PRIMARY KEY (catNodeID, pathRev)',
        'relations'   : 'relId INTEGER, pathRev INTEGER, relPrefix BLOB, relName BLOB, dMetaName0 BLOB, dMetaName1 BLOB, direction BLOB, validForLatest INTEGER, PRIMARY KEY (relId, pathRev)',
        'relVariants'   : 'relVarId INTEGER, pathRev INTEGER, relId INTEGER, relVarPrefix BLOB, relVarName BLOB, dMetaName0 BLOB, dMetaName1 BLOB, varDirection BLOB, validForLatest INTEGER, PRIMARY KEY (relVarId, pathRev)',
        'catConnections' : 'catConnId INTEGER, pathRev INTEGER, catNodeId INTEGER, superCatNodeId INTEGER, relVarId INTEGER, connStyleId INTEGER, validForLatest INTEGER, PRIMARY KEY (catConnId, pathRev)',
        'pathRevs': 'pathRev INTEGER, startDateTime BLOB, openForChange INTEGER, PRIMARY KEY (pathRev)',

        'fonts': 'fontID INTEGER, pathRev INTEGER, family BLOB, style BLOB, size INTEGER, color BLOB, validForLatest INTEGER, PRIMARY KEY (fontID, pathRev)',
        'nodeStyles': 'nodeStyleId INTEGER, pathRev INTEGER, styleName BLOB, dMetaName0 BLOB, dMetaName1 BLOB, fontID INTEGER, backgroundColor BLOB, transparency INTEGER, validForLatest INTEGER, PRIMARY KEY (nodeStyleId, pathRev)',
        'connectionStyles': 'connStyleId INTEGER, pathRev INTEGER, styleName BLOB, fontID INTEGER, headType BLOB, tailType BLOB, tailColor BLOB, transparency INTEGER, validForLatest INTEGER, PRIMARY KEY (connStyleId, pathRev)',
#    'newIdeas': 'id INTEGER PRIMARY KEY AUTOINCREMENT, noteText BLOB, date BLOB, owner BLOB',
#    'toDo'    : 'id INTEGER PRIMARY KEY AUTOINCREMENT, noteText BLOB, date BLOB, owner BLOB, completeByDate BLOB'
    }

    tableInits = {
        #             catId, pathRev, catName, dMetaName0, dMetaName1, validForLatest
        'categories'   : (0,       0,    None,         '',         '',              0),
        #              VarId, pathRev, catId, catName, dMetaName0, dMetaName1, validForLatest
        'catVariants'   : (0,       0,     0,    None,         '',         '',              0),
        #       catNodeId, pathRev, catVarId,   dx,   dy,   dz, nodeStyleId, validForLatest
        'catNodes'   : (0,       0,        0, None, None, None,           0,              0),
        #          relId*, pathRev*, prefix, relName, dMetaName0, dMetaName1, direction, validForLatest
        'relations'  : (0,        0,   None,    None,         '',         '',      None,              0),
        #relVarId*, pathRev*, relId, relVarPrefix, relVarName, dMetaName0, dMetaName1, varDirection, validForLatest
        'relVariants'  : (0,        0,     0,         None,       None,         '',         '',         None,              0),
        #catConnId*, pathRev*, catNodeId, relVarId, superCatNodeId, connStyleId, validForLatest
        'catConnections' : (0, 0, 0, 0, None, 0, 0),
        'pathRevs': (1, int(time.time()), 1),
        'fonts': (0, 1, 'Liberation Sans', 'Regular', 10, 'black', 1), #default comes from LibreOffice Calc
        'nodeStyles': (0, 1, 'default', 'TFLT', '', 0, 'white', 0, 1),
        'connectionStyles': (0, 1, 'default', 0, None, 'arrow', 'black', 0, 1),
    }

    typeInt = type(1)
    typeStr = type('s')
    
    def __init__(self, database_path_and_file_name, lock, in_memory = False, create_new_database = False):
        show = False
        if show: print('in CategorizerData.__init__()')
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

        # make the sql for adding entries and dumping the contents of the tables, e.g.
        #   INSERT INTO categories (catId, pathRev, catName, validForLatest) VALUES (?, ?, ?, ?)
        #   SELECT catId, pathRev, catName, validForLatest from categories
        
        # make lists of column names so the can be used by index
        #   columnNames ('catId', 'pathRev', 'catName', 'validForLatest')

        self.sqlAdds = {}
        self.sqlDumps = {}
        self.columnNames = {}
        for tableName in self.columnSpecs.keys():
            columnSpec = self.columnSpecs[tableName]
            namesVarTypes = columnSpec.split()
            primaryIdx = namesVarTypes.index('PRIMARY')
            namesVarTypes = namesVarTypes[:primaryIdx]
            names = tuple([ namesVarTypes[idx] for idx in range(0, len(namesVarTypes), 2) ])
            self.columnNames[tableName] = names
            self.sqlAdds[tableName] = f'INSERT INTO {tableName} ({", ".join(names)}) VALUES ({", ".join(["?"] * (len(names)))})'
            self.sqlDumps[tableName] = f'SELECT {", ".join(names)} from {tableName}'
            if show:
                print('  tableName', tableName, ': columnSpecs', self.columnSpecs[tableName])
                print('    sqlAdd', self.sqlAdds[tableName])
                print('    sqlDump', self.sqlDumps[tableName])
                print('    columnNames', self.columnNames[tableName])

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

    def _getPathRev(self):
        # get the pathRev
        cursor = self.dbCursor.execute('SELECT MAX(' + self.columnNames['pathRevs'][0] + ') FROM pathRevs')
        (pathRev,) = cursor.fetchone()
        cursor = self.dbCursor.execute('SELECT ' + self.columnNames['pathRevs'][2] + ' FROM pathRevs')
        (openForChange,) = cursor.fetchone()
        if openForChange:
            pass
        else:
            # make a new pathRev, add it to pathRevs and mark it open
            pathRev += 1
            self.dbCursor.execute(self.sqlAdds['pathRevs'], (pathRev, int(time.time()), 1))
        return pathRev
    
    def addCatNode(self, cat_var_id = None, cat_var_name = None, dx = None, dy = None, dz = None, nodeStyleId = 0):
        '''
        should the API enforce exclusive or?
        Add a single new catNode with no connections.
        Must have either cat_var_id or cat_var_name.
        If cat_var_id is provided, will add a catNode with that catVarId.
        If cat_var_name is provided, add a new category, catVariant, then add a catNode with the new catVarId.
        The application code should find the cat_var_id before calling this method.  If it cannot find it, then call this method with a cat_var_name, and a new category and category variant will be created.
        '''
        if cat_var_id:
            catNodeId = self._addCatNode(cat_var_id, dx, dy, dz, nodeStyleId)
        elif cat_var_name:
            catVarId = self._addCategory(cat_var_name) #adds category and catVariant and returns catVarId
            catNodeId = self._addCatNode(catVarId, dx, dy, dz, nodeStyleId)
        else:
            print('ERROR must provide either cat_var_id or cat_var_name')
            assert False
        return catNodeId

    def addConnection(self, cat_node_id, super_cat_node_id, rel_var_id = None, rel_var_name = None, conn_style_id = None):
        '''
        add a connection between two cat nodes.
        if rel_var_id is specified, use it for the relation and ignore rel_var_name
        if rel_var_id is not specified and rel_var_name is specified, look for the relation variant with that name.
          if the relation variant is not found, make a new relation and relation variant
          if the relation variant is found, get the relVarId and use it
        if neither rel_var_id or rel_var_name is specified, use relation variant id 0.

        After the connection is added, the dx, dy are determined by the GUI software and the editCatNode() is called with the dx, dy values.
        '''
        show = False
        if show: print('in addConnection() with cat_node_id', cat_node_id, ', super_cat_node_id', super_cat_node_id, ', rel_var_id', rel_var_id, ', rel_var_name', rel_var_name)
        pathRev = self._getPathRev()
        if rel_var_id == None:
            if rel_var_name == None:
                rel_var_id = 0
            else:
                rel_var_id = self._getRelVarId(rel_var_name)
                
        if conn_style_id == None:
            conn_style_id = 0

        #get the next catConnId
        cursor = self.dbCursor.execute('SELECT MAX(' + self.columnNames['catConnections'][0] + ') FROM catConnections')
        (catConnId,) = cursor.fetchone()
        catConnId += 1
        if show: print('  catConnId', catConnId, ', pathRev', pathRev)
        
        self.dbCursor.execute(self.sqlAdds['catConnections'], (catConnId, pathRev, cat_node_id, super_cat_node_id, rel_var_id, conn_style_id, 1))
        self.db.commit()
        return catConnId

    def editConnection(self, cat_conn_id, cat_node_id = None, super_cat_node_id = None, rel_var_id = None, rel_var_name = None, conn_style_id = None):
        show = False
        if show: print('in editConnection() with cat_conn_id', cat_conn_id, ', cat_node_id', cat_node_id, ', super_cat_node_id', super_cat_node_id, ', rel_var_id', rel_var_id, ', rel_var_name', rel_var_name)
        
        pathRev = self._getPathRev()

        # if we got a rel_var_name, convert it to a rel_var_id
        if rel_var_id == None:
            if rel_var_name == None:
                pass
            else:
                rel_var_id = self._getRelVarId(rel_var_name)
        # note: if we were passed both a rel_var_id and a rel_var_name, we ignore the rel_var_name
        
        (rowPathRev, sqlWhere) = self._getRowPathRevAndSQLWhere('catConnections', cat_conn_id)
        if rowPathRev == pathRev:
            # edit the existing row
            if show: print('  rowPathRev == pathRev, updating data:')
            colValPairs = []
            if cat_node_id != None:
                colValPairs.append( (self.columnNames['catConnections'][2], '\"' + str(cat_node_id) + '\"') )
            if super_cat_node_id != None:
                colValPairs.append( (self.columnNames['catConnections'][3], '\"' + str(super_cat_node_id) + '\"') )
            if rel_var_id != None:
                colValPairs.append( (self.columnNames['catConnections'][4], '\"' + str(rel_var_id) + '\"') )
            if conn_style_id != None:
                colValPairs.append( (self.columnNames['catConnections'][5], '\"' + str(conn_style_id) + '\"') )
            self._editRow('catConnections', colValPairs, sqlWhere)
        else:
            if show: print('  rowPathRev != pathRev, marking existing row to not validForLatest and creating new row:')
            # get all the existing values from the current row
            (catConnIdName, pathRevName, catNodeIdName, superCatNodeIdName, relVarIdName, connStyleIdName) = self.columnNames['catConnections'][:6]
            sql = 'SELECT ({ccni}, {pr}, {cni}, {scni}, {rvi}, {csi} FROM catNodes '.format(ccni=catConnIdName, pr=pathRevName, cni=catNodeIdName, scni=superCatNodeIdName, rvi=relVaiIdName, csi=connStyleIdName) + sqlWhere
            cursor = self.dbCursor.execute(sql)
            (catConnId, rowPathRev, oldCatNodeId, oldSuperCatNodeId, oldRelVarId, oldConnStyleId) = cursor.fetchone()

            # mark the old row as no longer the latest
            name, value = self.columnNames['catConnections'][-1], 0
            sql = 'UPDATE catConnections set {col} = {val}'.format(col = name, val = value) + sqlWhere
            self.dbCursor.execute(sql)

            # create a new version of the catConnection which is a new row in the table.  We change one of the primary keys: pathRev
            if cat_node_id == None:
                catNodeId = oldCatNodeId
            else:
                catNodeId = cat_node_id
            if super_cat_node_id == None:
                superCatNodeId = oldSuperCatNodeId
            else:
                superCatNodeId = super_cat_node_id
            if rel_var_id == None:
                relVarId = oldRelVarId
            else:
                relVarId = rel_var_id
            if conn_style_id == None:
                connStyleId = oldConnStyleId
            else:
                connStyleId = conn_style_id
            self.dbCursor.execute(self.sqlAdds['catConnections'], (cat_conn_id, pathRev, catNodeId, superCatNodeId, relVarId, connStyleId, 1))
        self.db.commit()

    def _addCatNode(self, cat_var_id, dx, dy, dz, node_style_id):
        show = False
        if show: print('in _addCatNode() with cat_var_id', cat_var_id, ', dx', dx, ', dy', dy, ', dz', dz, 'node_style_id', node_style_id)        

        pathRev = self._getPathRev()

        # get the next catId
        cursor = self.dbCursor.execute('SELECT MAX(' + self.columnNames['catNodes'][0] + ') FROM catNodes')
        (catNodeId,) = cursor.fetchone()
        catNodeId += 1
        if show: print('  catNodeId', catNodeId, ', pathRev', pathRev)

        self.dbCursor.execute(self.sqlAdds['catNodes'], (catNodeId, pathRev, cat_var_id, dx, dy, dz, node_style_id, 1))
        if show:
            print('    added new catNode:', (catNodeId, pathRev, cat_var_id, dx, dy, dz, node_style_id, 1))
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
        sql = 'SELECT ' + self.columnNames['relVariants'][0] + ' FROM relVariants WHERE ' + self.columnNames['relVariants'][4] + ' = "' + rel_var_name + '"'
        if show: print('  sql', sql)
        cursor = self.dbCursor.execute(sql)
        data = cursor.fetchone()
        if data:
            #found an exact match of the name
            (relVarId,) = data
        else:
            sql = 'SELECT ' + self.columnNames['relations'][0] + ' FROM relations WHERE ' + self.columnNames['relations'][3] + ' = "' + rel_var_name + '"'
            if show: print('  sql', sql)
            cursor = self.dbCursor.execute(sql)
            data = cursor.fetchone()
            if data:
                # found an exact match of the name in the relations table
                (relId,) = data
                # find the default relVarId for this relation
                sql = 'SELECT ' + self.columnNames['relVariants'][0] + ' FROM relVariants WHERE ' + self.columnNames['relVariants'][2] + ' = ' + str(relId)# + ' AND ' + self.columnNames['relVariants'][4] + ' = "' + str(None) + '"'
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
        cursor = self.dbCursor.execute('SELECT MAX(' + self.columnNames['categories'][0] + ') FROM categories')
        (catId,) = cursor.fetchone()
        catId += 1
        if show: print('  catId', catId, ', pathRev', pathRev)
        (dMetaName0, dMetaName1) = self.getDMetaNames(cat_name)
        # add the category
        self.dbCursor.execute(self.sqlAdds['categories'], (catId, pathRev, cat_name, dMetaName0, dMetaName1, 1))
        if show:
            print('    added new category:', (catId, pathRev, cat_name, dMetaName0, dMetaName1, 1))

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
        cursor = self.dbCursor.execute('SELECT MAX(' + self.columnNames['catVariants'][0] + ') FROM catVariants')
        (catVarId,) = cursor.fetchone()
        catVarId += 1
        (dMetaName0, dMetaName1) = self.getDMetaNames(cat_var_name)
        self.dbCursor.execute(self.sqlAdds['catVariants'], (catVarId, pathRev, cat_id, cat_var_name, dMetaName0, dMetaName1, 1))
        self.db.commit()
        return catVarId

    def _addRelation(self, rel_prefix, rel_name, direction):
        show = False
        if show: print('in _addRelation() with rel_prefix', rel_prefix, ', rel_name', rel_name, ', direction', direction)
        pathRev = self._getPathRev()

        # get the next relId
        cursor = self.dbCursor.execute('SELECT MAX(' + self.columnNames['relations'][0] + ') FROM relations')
        (relId,) = cursor.fetchone()
        relId += 1
        if show: print('  relId', relId, ', pathRev', pathRev)

        # get the double metaphone code for rel_name
        (dMetaName0, dMetaName1) = self.getDMetaNames(rel_name)
        self.dbCursor.execute(self.sqlAdds['relations'], (relId, pathRev, rel_prefix, rel_name, dMetaName0, dMetaName1, direction, 1))
        if show:
            print('    added new relation:', (relId, pathRev, rel_prefix, rel_name, dMetaName0, dMetaName1, direction, 1))

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

        # add the relation variant for the relation
        cursor = self.dbCursor.execute('SELECT MAX(' + self.columnNames['relVariants'][0] + ') FROM relVariants')
        (relVarId,) = cursor.fetchone()
        relVarId += 1

        # get the double metaphone names
        (dMetaName0, dMetaName1) = self.getDMetaNames(rel_var_name)
        self.dbCursor.execute(self.sqlAdds['relVariants'], (relVarId, pathRev, rel_id, rel_var_prefix, rel_var_name, dMetaName0, dMetaName1, var_direction, 1))
        
        self.db.commit()
        return relVarId

    def getDMetaNames(self, name):
        if name == None:
            dMetaName0 = ''
            dMetaName1 = ''
        else:
            dMetaNames = self.dMeta(name)
            dMetaName0 = dMetaNames[0].decode()
            if dMetaNames[1] == None:
                dMetaName1 = ''
            else:
                dMetaName1 = dMetaNames[1].decode()
        return (dMetaName0, dMetaName1)
    
    def editCategory(self, cat_id, cat_name):
        '''
        Change the name of a category.  This is typically a small change, like capitalization, plural, or a more general term.
        It could also be a more specific term if the category is being split into two or more parts.  Then the other category(ies) would be added with addCatNode().
        '''
        show = False
        if show: print('in editCategory() with cat_id', cat_id, ', cat_name', cat_name)
        pathRev = self._getPathRev()
        (rowPathRev, sqlWhere) = self._getRowPathRevAndSQLWhere('categories', cat_id)
        (dMetaName0, dMetaName1) = self.getDMetaNames(cat_name)
        if rowPathRev == pathRev:
            if show: print('  rowPathRev == pathRev, updating data:')
            colValPairs = [
                (self.columnNames['categories'][2], '\"' + cat_name + '\"'), 
                (self.columnNames['categories'][3], '\"' + dMetaName0 + '\"'), 
                (self.columnNames['categories'][4], '\"' + dMetaName1 + '\"'), 
            ]
            self._editRow('categories', colValPairs, sqlWhere)
            #do I need to change the default catVariant (the one with None for a name also?) 
        else:
            if show: print('  rowPathRev != pathRev, marking existing row to not validForLatest and creating new row:')
            name, value = self.columnNames['categories'][-1], 0
            sql = 'UPDATE categories set {col} = {val}'.format(col = name, val = value) + sqlWhere
            self.dbCursor.execute(sql)
            self.dbCursor.execute(self.sqlAdds['categories'], (cat_id, pathRev, cat_name, 1))
        self.db.commit()
        
    def editCatVariant(self, cat_var_id, cat_var_name):
        '''
        Change the name of a category variant.  This is typically a small change, like capitalization, plural, or a more general term.
        It could also be a more specific term if the category variant is being split into two or more parts.  Then the other category(ies) / catVariant(s) would be added with addCatNode().
        '''
        show = False
        if show: print('in editCatVariant() with cat_var_id', cat_var_id, ', cat_var_name', cat_var_name)
        pathRev = self._getPathRev()
        (rowPathRev, sqlWhere) = self._getRowPathRevAndSQLWhere('catVariants', cat_var_id)
        (dMetaName0, dMetaName1) = self.getDMetaNames(cat_var_name)
        if rowPathRev == pathRev:
            if show: print('  rowPathRev == pathRev, updating data:')
            colValPairs = [
                (self.columnNames['catVariants'][3], '\"' + cat_var_name + '\"'),
                (self.columnNames['catVariants'][4], '\"' + dMetaName0 + '\"'),
                (self.columnNames['catVariants'][5], '\"' + dMetaName1 + '\"'),
            ]
            self._editRow('catVariants', colValPairs, sqlWhere)
            #do I need to change the default catVariant (the one with None for a name also?) 
        else:
            if show: print('  rowPathRev != pathRev, marking existing row to not validForLatest and creating new row:')
            name, value = self.columnNames['categories'][-1], 0
            sql = 'UPDATE catVariants set {col} = {val}'.format(col = name, val = value) + sqlWhere
            self.dbCursor.execute(sql)
            self.dbCursor.execute(self.sqlAdds['catVariants'], (cat_var_id, pathRev, cat_var_name, dMetaName0, dMetaName1, 1))
        self.db.commit()
        
    def editCatNode(self, cat_node_id, cat_var_id = None, cat_var_name = None, dx = None, dy = None, dz = None, node_style_id = None):
        '''
        Given a cat_node_id selected from the GUI, change one of more of; category variant id, dx, dy
        Just like addCatNode(), a new category can be created by passing a cat_var_name without a cat_var_id.

        if the pathRev of the catNode is current:
          simply change the current catNode

        if the pathRev of the catNode is not current:
          create a new catNode with the new pathRev and catVarId, cloning the rest of the data.
          create new catConnections with the new catNodeId and pathRev, cloning the rest of the data.
          mark the old catNode validForLatest = False
          mark the old catConnections' validForLatest = False
        '''
        show = False
        if show: print('in editCatNode() with cat_node_id', cat_node_id, ', cat_var_id', cat_var_id, ', dx', dx, ', dy', dy, ', dz', dz, 'node_style_id', node_style_id)
        if cat_var_id == None and dx == None and dy == None and dz == None and node_style_id == None:
            return

        # just like addCatNode, we can create a new category by passing a name without a cat_var_id
        if not cat_var_id and cat_var_name:
            cat_var_id = self._addCategory(cat_var_name)
            
        # get the latest pathRev
        pathRev = self._getPathRev()

        # get the path rev of the latest version of this catNode and the corresponding sql WHERE statement
        (rowPathRev, sqlWhere) = self._getRowPathRevAndSQLWhere('catNodes', cat_node_id) 

        if rowPathRev == pathRev:
            # The pathRevs are the same, so we can just change the existing tuple with what we need to change
            if show: print('    rowPathRev == pathRev, updating data:')
            colValPairs = []
            if cat_var_id != None:
                colValPairs.append( (self.columnNames['catNodes'][2], cat_var_id) )
            if dx != None:
                colValPairs.append( (self.columnNames['catNodes'][3], dx) )
            if dy != None:
                colValPairs.append( (self.columnNames['catNodes'][4], dy) )
            if dz != None:
                colValPairs.append( (self.columnNames['catNodes'][5], dz) )
            if node_style_id != None:
                colValPairs.append( (self.columnNames['catNodes'][6], node_style_id) )
            if show: print('  colValPairs', colValPairs)
            self._editRow('catNodes', colValPairs, sqlWhere)
        else:
            # The pathRevs are not the same, so we need to make a new tuple in the database
            if show: print('    rowPathRev != pathRev, marking existing row to not validForLatest and creating new row:')
            # get all the existing values from the current row
            (catNodeIdName, pathRevName, catVarIdName, dxName, dyName, dzName, nodeStyleIdName) = self.columnNames['catNodes'][:7]
            sql = 'SELECT ({cni}, {pr}, {cvi}, {dx}, {dy}, {dz} {nsID} FROM catNodes '.format(cni=catNodeIdName, pr=pathRevName, cvi=catVarIdName, dx=dxName, dy=dyName, dz=dzName, nsID=nodeStyleIDName) + sqlWhere
            cursor = self.dbCursor.execute(sql)
            (catNodeId, rowPathRev, oldCatVarId, oldDx, oldDy, oldDz, oldNodeStyleId) = cursor.fetchone()

            # set validForLatest of the old one to 0
            columnName, value = self.columnNames['catNodes'][-1], 0
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
            if dz == None:
                dz = oldDz
            if node_style_id == None:
                nodeStyleId = oldNodeStyleId
            self.dbCursor.execute(self.sqlAdds['catNodes'], (catNodeId, pathRev, catVarId, dx, dy, dz, nodeStyleId, 1))
        self.db.commit()

    def addNodeStyle(self, style_name, font_id = None, font_family = None, font_style = None, font_size = None, font_color = None, background_color = None, transparency = None):
        '''
        add a new style for a node.  If you wish to reuse an already existing font, you can specify it using its font_id which you can find using the findFont() method.
        If you wish to specify a font, use font_family, font_style, font_size, font_color.  If that font description already exists, its font_id will be found and used for this node style.
        If no font information is specified, the default font will be used.
        In addition to font, the background_color and transparency can be specified or left blank to use defaults.
        '''
        show = False
        if show: print('in addNodeStyle() with style_name', style_name, ', font_id', font_id, ', font_family', font_family, ', font_style', font_style, ', font_size', font_size, ', font_color', font_color, ', background_color', background_color, ', transparency', transparency)
        pathRev = self._getPathRev()
        cursor = self.dbCursor.execute('SELECT MAX(' + self.columnNames['nodeStyles'][0] + ') FROM nodeStyles')
        (nodeStyleId,) = cursor.fetchone()
        nodeStyleId += 1
        if show: print('  nodeStyleId', nodeStyleId, ', pathRev', pathRev)

        # if we do not have a font_id, and we have other font info, create a new font
        if font_id == None:
            if not (font_family == None and font_style == None and font_size == None and font_color == None):
                # see if we have an exact match already in the fonts table
                colValPairs = []
                colValPairs.append( (self.columnNames['fonts'][2], font_family) )
                colValPairs.append( (self.columnNames['fonts'][3], font_style) )
                colValPairs.append( (self.columnNames['fonts'][4], font_size) )
                colValPairs.append( (self.columnNames['fonts'][5], font_color) )
                rowIds = self._getMatchingRowIds('fonts', colValPairs)
                if rowIds:
                    if show: print('    found an exact match for the font description')
                    # found an exact match, use that fontId
                    fontId = rowIds[-1]
                else:
                    # create a new font
                    if show: print('   did not find a match for the font description, creating a new font')
                    fontId = self._addFont(font_family, font_style, font_size, font_color)
            else:
                fontId = 0
        else:
            fontId = font_id
        (dMetaName0, dMetaName1) = self.getDMetaNames(style_name)
        self.dbCursor.execute(self.sqlAdds['nodeStyles'], (nodeStyleId, pathRev, style_name, dMetaName0, dMetaName1, fontId, background_color, transparency, 1))
        self.db.commit()
        return nodeStyleId

    def _addFont(self, font_family, font_style, font_size, font_color):
        show = False
        if show: print('in _addFont() with font_family', font_family, ', font_style', font_style, ', font_size', font_size, ', font_color', font_color)

        pathRev = self._getPathRev()

        # get the next fontId
        cursor = self.dbCursor.execute('SELECT MAX(' + self.columnNames['fonts'][0] + ') FROM fonts')
        (fontId,) = cursor.fetchone()
        fontId += 1
        if show: print('  fontId', fontId, ', pathRev', pathRev)

        self.dbCursor.execute(self.sqlAdds['fonts'], (fontId, pathRev, font_family, font_style, font_size, font_color, 1))
        if show:
            print('    added new font:', (fontId, pathRev, font_family, font_style, font_size, font_color, 1))
        return fontId

    def findCatVariantIds(self, name, only_latest = False):
        '''
        Based on the sound of the name, search the categories and catVariants for matches.  
        If the name is found in the categories, get the catId and find all the catVariants which have the catId and record the catVarId.
        If the name is found in the catVariants, get the catId and find all the catVariants which have the catId and record the catVarId.
        if only_latest is False, skip any catVarIds which do not exist with a latest flag.
        return a tuple of catVarIds
        '''
        pass
    
    def _getMatchingRowIds(self, table_name, col_val_pairs, only_valid_for_latest = True):
        show = False
        if show: print('in _getMatchingRowIds() with table_name', table_name, ', col_val_pairs', col_val_pairs, ', only_valid_for_latest', only_valid_for_latest)
        sqlWhere = ' WHERE '
        for (colName, colVal) in col_val_pairs:
            if type(colVal) == self.typeStr:
                sqlWhere += colName + ' == "' + colVal + '" AND '
            else:
                sqlWhere += colName + ' == ' + str(colVal) + ' AND '
        if only_valid_for_latest:
            sqlWhere += 'validForLatest == 1'
        else:
            sqlWhere = sqlWhere[:-5]
        if show: print('  sqlWhere', sqlWhere)
#        sql = 'SELECT ' + self.columnNames[table_name][0] + ', ' + self.columnNames[table_name][1] + ' FROM ' + table_name + sqlWhere
        sql = 'SELECT ' + self.columnNames[table_name][0] + ' FROM ' + table_name + sqlWhere
        if show: print('  sql:', sql)
        try:
            cursor = self.dbCursor.execute(sql)
        except sqlite3.OperationalError as e:
            if show: print('  row not found, returning')
            return tuple()
        
        rowIds = []
        while True:
            data = cursor.fetchone()
            if data:
                rowIds.append(data[0])
            else:
                break
        return tuple(rowIds)
    
    def _getRowPathRevAndSQLWhere(self, table_name, row_id):
        '''
        the 1st column of all tables must be an id
        the 2nd column of all tables must be pathRev
        the last column of all tables must be validForLatest
        '''
        show = False
        if show: print('in _getRowPathRevAndSQLWhere() with table_name', table_name, ', row_id', row_id)
        columnNames = self.columnNames[table_name]
        sqlWhere = ' WHERE ' + columnNames[0] + ' == ' + str(row_id) + ' AND ' + columnNames[-1] + ' == 1'
        sql = 'SELECT ' + columnNames[1] + ' FROM ' + table_name + sqlWhere
        if show: print('  sql:', sql)
        cursor = self.dbCursor.execute(sql)
        (rowPathRev,) = cursor.fetchone()
        if show: print('  returning (rowPathRev', rowPathRev, ', sqlWhere', sqlWhere, ')')
        return (rowPathRev, sqlWhere)
    
    def _editRow(self, table_name, column_value_pairs, sql_where):
        show = False
        if show: print('in _editRow() with table_name', table_name, ', column_value_pairs', column_value_pairs, ', sql_where', sql_where)
        sql = 'UPDATE ' + table_name + ' SET'
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
        if show:
            print('sqlAdds', self.sqlAdds[table_name])
            print('tableInits', self.tableInits[table_name])
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
