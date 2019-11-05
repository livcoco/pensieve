'''
history
12/19/18 - 
    add try for test01, 
    r'SELECT... == "{}"'.format(catname)
    change to try: instead of return False

'''
import unittest
import multiprocessing
from context import CategorizerData
import shutil

class DataStoragePathTest(unittest.TestCase):
    runAll = False
    runTestCounts = [0, 1, 2, 3, 4]
    runTestCounts = [5,6]
    runTestCounts = [1,2,3,4,5,6,7]
    runTestCounts = [1,2,3,4,5,6,7,8]
    
    def test_00_instantiate(self):
        if not self.runAll:
            if 0 not in self.runTestCounts:
                return
        print('  test_00_instantiate')
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        
    def test_01_createFromScratch(self):
        # always have to run this test to create a new database

        #if not self.runAll:
        #    if 1 not in self.runTestCounts:
        #        return
        print('  test_01_create_from_scratch')
        path = './test.db'
        try:
            shutil.move(path, path + '.bak')
        except FileNotFoundError:
            pass
        
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock, create_new_database = True)
        
    def test_02_addCategory(self):
        if not self.runAll:
            if 2 not in self.runTestCounts:
                return
        show = False
        print('  test_02_addCategory')
        expCats = (
            #catId, pathRev, catName, validForLatest
            (0, 0,    None, 0),
            (1, 1,  'Farm', 1),
            (2, 1, 'Horse', 1),
            (3, 1,   'Pig', 1),
            (4, 1,   'Dog', 1),
        )
        expCatVars = (
            #catVarId, pathRev, catId, catVarName, validForLatest
            (0, 0, 0,   None, 0),
            (1, 1, 1,   None, 1),
            (2, 1, 2,   None, 1),
            (3, 1, 3,   None, 1),
            (4, 1, 4,   None, 1),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for i in range(1, len(expCats)):
            cat = expCats[i][2]
            db._addCategory(cat)
        actCats = db.dumpTable('categories')
        self.compareTuples('categories', expCats, actCats, show)
        actCatVars = db.dumpTable('catVariants')
        self.compareTuples('catVariants', expCatVars, actCatVars, show)

    def test_03_addCategoryVariant(self):
        if not self.runAll:
            if 3 not in self.runTestCounts:
                return
        show = False
        print('  test_03_addCategoryVariant')
        addCatVars = (
            #skip variant for Farm
            (5, 1, 2,  'horsey', 1),
            (6, 1, 3,   'piggy', 1),
            (7, 1, 4,  'doggie', 1),
        )
        expCatVars = (
            #catVarId, pathRev, catId, catName, validForLatest
            (0, 0, 0,      None, 0),
            (1, 1, 1,      None, 1),
            (2, 1, 2,      None, 1),
            (3, 1, 3,      None, 1),
            (4, 1, 4,      None, 1),
            #skip variant for Farm
            (5, 1, 2,  'horsey', 1),
            (6, 1, 3,   'piggy', 1),
            (7, 1, 4,  'doggie', 1),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for i in range(len(addCatVars)):
            catId = addCatVars[i][2]
            catVarName = addCatVars[i][3]
            db._addCatVariant(catId, catVarName)
        actCatVars = db.dumpTable('catVariants')
        self.compareTuples('catVariants', expCatVars, actCatVars, show)

    def test_04_addCatNode(self):
        if not self.runAll:
            if 4 not in self.runTestCounts:
                return
        show = False
        print('  test_04_addCatNode')
        addCatNodes = (
            #cat_var_id, cat_var_name
            (1, None),
            (2, None),
            (5, None),
            (6, None),
            (None, 'cow'),
            (None, 'sheep'),
        )
        expCatNodes = (
            #catNodeId, pathRev, catVarId, dx, dy, validForLatest
            (0, 0, 0,  None, None, 0),
            (1, 1, 1,  None, None, 1),
            (2, 1, 2,  None, None, 1),
            (3, 1, 5,  None, None, 1),
            (4, 1, 6,  None, None, 1),
            (5, 1, 8,  None, None, 1),
            (6, 1, 9,  None, None, 1),
        )
        expCats = (
            #catId, pathRev, catName, validForLatest
            (0, 0,    None, 0),
            (1, 1,  'Farm', 1),
            (2, 1, 'Horse', 1),
            (3, 1,   'Pig', 1),
            (4, 1,   'Dog', 1),
            (5, 1,   'cow', 1),
            (6, 1,   'sheep', 1),
        )
        expCatVars = (
            #catVarId, pathRev, catId, catName, validForLatest
            (0, 0, 0,      None, 0),
            (1, 1, 1,      None, 1),
            (2, 1, 2,      None, 1),
            (3, 1, 3,      None, 1),
            (4, 1, 4,      None, 1),
            #skip variant for Farm
            (5, 1, 2,  'horsey', 1),
            (6, 1, 3,   'piggy', 1),
            (7, 1, 4,  'doggie', 1),
            (8, 1, 5,  None, 1),
            (9, 1, 6,  None, 1),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for i in range(len(addCatNodes)):
            catNodeId = addCatNodes[i][0]
            catVarName = addCatNodes[i][1]
            db.addCatNode(catNodeId, catVarName)
        actCatNodes = db.dumpTable('catNodes')
        self.compareTuples('catNodes', expCatNodes, actCatNodes, show)
        actCats = db.dumpTable('categories')
        self.compareTuples('categories', expCats, actCats, show)
        actCatVars = db.dumpTable('catVariants')
        self.compareTuples('catVariants', expCatVars, actCatVars, show)
        
    def test_05_addRelation(self):
        if not self.runAll:
            if 5 not in self.runTestCounts:
                return
        show = False
        print('  test_05_addRelation')
        expRels = (
            #relId*, pathRev*, prefix, relName, validForLatest
            (0, 0, None, None, None, 0),
            (1, 1, 'hyper', 'is-a', 'out', 1),
            (2, 1, 'super', 'has-a', 'in', 1),
            (3, 1, 'pre', 'prior in sequence', 'out',1),
            (4, 1, 'pre', 'prior in cycle', 'out', 1),
        )
        expRelVars = (
            #relVarId*, pathRev*, relId, relVarPrefix, relVarName, varDirection, validForLatest
            (0, 0, 0,   None, None, None, 0),
            (1, 1, 1,   None, None, None, 1),
            (2, 1, 2,   None, None, None, 1),
            (3, 1, 3,   None, None, None, 1),
            (4, 1, 4,   None, None, None, 1),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for i in range(1, len(expRels)):
            rel = expRels[i]
            db._addRelation(rel[2], rel[3], rel[4])
        actRels = db.dumpTable('relations')
        self.compareTuples('relations', expRels, actRels, show)
        actRelVars = db.dumpTable('relVariants')
        self.compareTuples('relVariants', expRelVars, actRelVars, show)

    def test_06_addRelationVariant(self):
        if not self.runAll:
            if 6 not in self.runTestCounts:
                return
        show = False
        print('  test_06_addRelationVariant')
        addRelVars = (
            #skip variant for Farm
            (5, 1, 2, None, 'reverse has-a', 'out', 1),
            (6, 1, 3, 'prePIS', 'PIS', None, 1),
            (7, 1, 4, 'prePIC', 'PIC', None, 1),
        )
        expRelVars = (
            #relVarId, pathRev, relId, relVarPrefix, relVarName, varDirection, validForLatest
            (0, 0, 0, None, None, None, 0),
            (1, 1, 1, None, None, None, 1), #default for relId 1, e.g. 'is-a'
            (2, 1, 2, None, None, None, 1), #default for relId 2, e.g. 'has-a'
            (3, 1, 3, None, None, None, 1), #default for relId 3, e.g. 'prior in sequence'
            (4, 1, 4, None, None, None, 1), #default for relId 4, e.g. 'prior in cycle'
            (5, 1, 2, None, 'reverse has-a', 'out', 1), #new relation variant for relId 2 with new direction
            (6, 1, 3, 'prePIS', 'PIS', None, 1), #new relation variant for relId 3
            (7, 1, 4, 'prePIC', 'PIC', None, 1), #new relation variant for relId 4
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for i in range(len(addRelVars)):
            relVars = addRelVars[i]
            db._addRelVariant(relVars[2], relVars[3], relVars[4], relVars[5])
        actRelVars = db.dumpTable('relVariants')
        self.compareTuples('relVariants', expRelVars, actRelVars, show)

    def test_07_addConnection(self):
        '''
        add a connection between catNodes
        find the relation for the connection if it exists
        make a new relation if it does not exist.
        '''
        if not self.runAll:
            if 7 not in self.runTestCounts:
                return
        necessaryPreTests = set([1,2,3,4,5,6])
        if necessaryPreTests != set(self.runTestCounts).intersection(necessaryPreTests):
            print('ERROR - to run test_07, must run tests', necessaryPreTests)
        show = False
        print('  test_07_addConnection')
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        addConns = (
            #catNodeId, superCatNodeId, relVarId
            (4, 3, 3, None), #1 create a connection from relVarId 3, i.e. 
            (4, 3, 0, None), #2 just make an unspecified connection, (default relationVariant)
            (4, 3, None, 'reverse has-a'), #3 make a connection based on an existing relVarName
            (4, 3, None, 'is-a'), #4 make a connection based on an existing relation Name
            (4, 3, None, 'from'), #5 make a connection based on a new relation Name
            )
        expCatConns = (
            #catNodeId, pathRev, relVarId, superCatNodeId, validForLatest
            (0, 0, 0, None, 0), #default, always there. created during database init
            (4, 1, 3, 3, 1), #1
            (4, 1, 0, 3, 1), #2
            (4, 1, 5, 3, 1), #3
            (4, 1, 1, 3, 1), #4
            (4, 1, 8, 3, 1), #5
        )
        for (catNodeId, superCatNodeId, relVarId, relVarName) in addConns:
            #                from       to              use one of these or neither
            db.addConnection(catNodeId, superCatNodeId, relVarId, relVarName)
        actCatConns = db.dumpTable('catConnections')
        self.compareTuples('catConnections', expCatConns, actCatConns, show)

    def test_08_editCatNode(self):
        '''
        things we can change on a catNode
          catVarId
          dx
          dy
        will not create new categories or category variants.   
        '''
        if not self.runAll:
            if 8 not in self.runTestCounts:
                return
        necessaryPreTests = set([1,2,3,4,5,6,7])
        if necessaryPreTests != set(self.runTestCounts).intersection(necessaryPreTests):
            print('ERROR - to run test_08, must run tests', necessaryPreTests)
        show = True
        print('  test_08_editCatNode')
        editCatNodes = (
            #catNodeId, newCatVarId, newDx, newDy
            (1, 2, None, None), #change from 1: 'Farm' to 2: 'Horse'
            (2, 5, None, None), #change from 2: 'Horse' to 5: 'Horsey'
            (3, 5, 22, None), # change dx to 22
            (4, 6, None, 37), # change dy to 37
            (5, 6, 11, 15), # change catVarId 6, dx to 11, dy 15
        )
        expCatNodes = (
            #catNodeId, pathRev, catVarId, dx, dy, validForLatest
            (0, 0, 0,  None, None, 0),
            (1, 1, 2,  None, None, 1), # catVarId to '2'
            (2, 1, 5,  None, None, 1), # catVarId to '5'
            (3, 1, 5,  22, None, 1), # dx to 22
            (4, 1, 6,  None, 37, 1), # dy to 37
            (5, 1, 6,  11, 15, 1), # catVarId 6, dx 11, dy 15
            (6, 1, 9,  None, None, 1),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for (catNodeId, newCatVarId, newDx, newDy) in editCatNodes:
            db.editCatNode(catNodeId, newCatVarId, newDx, newDy)
        actCatNodes = db.dumpTable('catNodes')
        self.compareTuples('catNodes', expCatNodes, actCatNodes, show)
        
    def REDOtest_03_addNodesWithNodeName(self):
        if not self.runAll:
            if 3 not in self.runTestCounts:
                return
        show = False
        if show: print('  test_03_addNodes')
        expNodesTuples = (
            (0, 0,    None,    None, 1),
            (1, 1,  'Farm',  'farm', 1),
            (2, 2, 'Horse', 'horse', 1),
            (3, 2,   'Pig',   'pig', 1),
            (4, 2,   'Dog',   'dog', 1),
        )
        expPreNodesTuples = (
            (0, 0, None, None, None, None, 1),
            (1, 1, None, None, None, None, 1),
            (2, 2, 1, 1, 1, None, 1),
            (3, 2, 1, 1, 1, None, 1),
            (4, 2, 1, 1, 1, None, 1),
        )
        expCategoriesTuples = (
            (0, None, None),
            (1, 1, 'animals')
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        category = 'animals'
        nodes = ('Horse', 'Pig', 'Dog')
        preNode = 'Farm'
#        db.addNodes((preNode,), None, None)
        db.addNode(preNode)
        db.addNodes(nodes, category_name = category, pre_node_name = preNode)
        actNodesTuples = db.dumpTable('nodes')
        self.compareTuples('nodes', expNodesTuples, actNodesTuples, show)

        actPreNodesTuples = db.dumpTable('preNodes')
        self.compareTuples('preNodes', expPreNodesTuples, actPreNodesTuples, show)

        actCategoriesTuples = db.dumpTable('categories')
        self.compareTuples('categories', expCategoriesTuples, actCategoriesTuples, show)
        
    def REDOtest_04_getNodeIds(self):
        if not self.runAll:
            if 4 not in self.runTestCounts:
                return
        show = False
        if show: print('  test_04_getNodeIds')
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        expNodeId = (2,)
        actNodeId = db.getNodeIds('horse')
        if show:
            print('    horse nodeId, exp:', expNodeId, ', act', actNodeId, end=' ')
            if expNodeId != actNodeId:
                print('********************************* ERROR ****************************')
            else: print()
        else:
            self.assertEqual(expNodeId, actNodeId)

    def REDOtest_05_addNodesWithNodeId(self):
        if not self.runAll:
            if 5 not in self.runTestCounts:
                return
        show = False
        if show: print('  test_05_addNodesWithNodeId')
        expNodesTuples = (
            (0, 0, None, None, None, 1),
            (1, 1, 'farm', 1, 0, 1),
            (2, 2, 'horse', 1, 0, 1),
            (3, 2, 'pig', 1, 1, 1),
            (4, 2, 'dog', 1, 2, 1),
            (5, 3, 'Quarter horse', 1, 0, 1),
            (6, 3, 'Mustang', 1, 1, 1),
            (7, 3, 'Appaloosa', 1, 2, 1),
            (8, 3, 'Morgan horse', 1, 3, 1),
        )
        expPreNodesTuples = (
            (0, 0, None, None, None, None, 1),
            (1, 1, None, None, None, None, 1),
            (2, 2, 1, 1, 1, None, 1),
            (3, 2, 1, 1, 1, None, 1),
            (4, 2, 1, 1, 1, None, 1),
            (5, 3, 2, 2, 2, None, 1),
            (6, 3, 2, 2, 2, None, 1),
            (7, 3, 2, 2, 2, None, 1),
            (8, 3, 2, 2, 2, None, 1),
        )
        expCategoriesTuples = (
            (0, None, None),
            (1, 1, 'animals'),
            (2, 2, 'Horse Breeds'),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        nodeId = db.getNodeIds('horse')[0]
        category = 'Horse Breeds'
        nodes = ('Quarter horse', 'Mustang', 'Appaloosa', 'Morgan horse')
        preNodeId = nodeId
        db.addNodes(nodes, category, pre_node_id = preNodeId)
        actNodesTuples = db.dumpTable('nodes')
        self.compareTuples('nodes', expNodesTuples, actNodesTuples, show)

        actPreNodesTuples = db.dumpTable('preNodes')
        self.compareTuples('nodes', expPreNodesTuples, actPreNodesTuples, show)

    def REDOtest_05_addNodesToCategory(self):
        if not self.runAll:
            if 5 not in self.runTestCounts:
                return
        show = False
        if show: print('  test_05_addNodesToCategory')
        expNodesTuples = (
            (0, 0, None, None, None, 1),
            (1, 1, 'farm', 1, 0, 1),
            (2, 2, 'horse', 1, 0, 1),
            (3, 2, 'pig', 1, 1, 1),
            (4, 2, 'dog', 1, 2, 1),
            (5, 3, 'Quarter horse', 1, 0, 1),
            (6, 3, 'Mustang', 1, 1, 1),
            (7, 3, 'Appaloosa', 1, 2, 1),
            (8, 3, 'Morgan horse', 1, 3, 1),
            (9, 4, 'sheep', 1, 0, 1),
        )
        expPreNodesTuples = (
            (0, 0, None, None, None, None, 1),
            (1, 1, None, None, None, None, 1),
            (2, 2, 1, 1, 1, None, 1),
            (3, 2, 1, 1, 1, None, 1),
            (4, 2, 1, 1, 1, None, 1),
            (5, 3, 2, 2, 2, None, 1),
            (6, 3, 2, 2, 2, None, 1),
            (7, 3, 2, 2, 2, None, 1),
            (8, 3, 2, 2, 2, None, 1),
            (9, 4, 1, 1, 1, None, 1)
        )
        expCategoriesTuples = (
            (0, None, None),
            (1, 1, 'animals'),
            (2, 2, 'Horse Breeds'),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        category = 'animals'
        nodes = ('sheep',)
        preNode = 'farm'
        db.addNodesToCategory(nodes, category_name = category, pre_node_name = preNode)

        actNodesTuples = db.dumpTable('nodes')
        self.compareTuples('nodes', expNodesTuples, actNodesTuples, show)

        actPreNodesTuples = db.dumpTable('preNodes')
        self.compareTuples('nodes', expPreNodesTuples, actPreNodesTuples, show)

        actCategoriesTuples = db.dumpTable('categories')
        self.compareTuples('nodes', expCategoriesTuples, actCategoriesTuples, show)
        
    def REDOtest_06_getNodeInfo(self):
        if not self.runAll:
            if 6 not in self.runTestCounts:
                return
        show = False
        if show: print('  test_06_getNodeInfo')
        expNodeInfo = (
            ('dog', ((4, 'dog', 1, 'animals', None, 1, 'farm'),)),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)

        for (nodeName, expNodeInfo) in expNodeInfo:
            actNodeInfo = db.getNodeInfo(nodeName)
            if show:
                print('  expNodeInfo', expNodeInfo)
                print('  actNodeInfo', actNodeInfo)
            else:
                self.assertEqual(expNodeInfo, actNodeInfo)
                
    def compareTuples(self, tuplesName, expTuples, actTuples, show):
        if show:
            print('   ', tuplesName,':')
            showErrorCnt = 0
            for (expTuple, actTuple) in zip(expTuples, actTuples):
                print('      exp:', expTuple, ', act:', actTuple, end=' ')
                if expTuple != actTuple:
                    showErrorCnt += 1
                    print('******************************** ERROR ****************************')
                else: print()
            #print('TMPDEBUG', len(expTuple), len(actTuple))
            if len(expTuples) != len(actTuples):
                showErrorCnt += 1
                numExp = len(expTuples)
                numAct = len(actTuples)
                print('    there are', numExp, 'expected data and', numAct, 'actual data.  ************************************* ERROR **************************')
                if numExp > numAct:
                    for expDataIdx in range(numAct, numExp):
                        print('      extra exp:', expTuples[expDataIdx])
                else:
                    for actDataIdx in range(numExp, numAct):
                        print('      extra act:', actTuples[actDataIdx])
                        
            print('  got', showErrorCnt, 'ERRORS')
        else:
            self.assertEqual(expTuples, actTuples)
        
if __name__ == '__main__':
    unittest.main()
