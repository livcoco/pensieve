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
    
    def test_00_instantiate(self):
        if not self.runAll:
            if 0 not in self.runTestCounts:
                return
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        
    def test_01_createFromScratch(self):
        # always have to run this test to create a new database

        #if not self.runAll:
        #    if 1 not in self.runTestCounts:
        #        return
        path = './test.db'
        try:
            shutil.move(path, path + '.bak')
        except FileNotFoundError:
            pass
        
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock, create_new_database = True)
        
    def test_02_addCategories(self):
        if not self.runAll:
            if 2 not in self.runTestCounts:
                return
        show = True
        if show: print('  test_02_addCategories')
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

    def test_03_addCategoryVariants(self):
        if not self.runAll:
            if 3 not in self.runTestCounts:
                return
        show = True
        if show: print('  test_03_addCategoryVariants')
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

    def test_04_addCatNodes(self):
        if not self.runAll:
            if 4 not in self.runTestCounts:
                return
        show = True
        if show: print('  test_04_addCatNodes')
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
            print('  ', tuplesName,':')
            for (expTuple, actTuple) in zip(expTuples, actTuples):
                print('      exp:', expTuple, ', act:', actTuple, end=' ')
                if expTuple != actTuple:
                    print('******************************** ERROR ****************************')
                else: print()
        else:
            self.assertEqual(expTuples, actTuples)
        
if __name__ == '__main__':
    unittest.main()
