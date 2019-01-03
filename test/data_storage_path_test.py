'''
history
12/19/18 - 
    add try for test01, 
    r'SELECT... == "{}"'.format(catname)
    change to try: instead of return False

'''
import unittest
import multiprocessing
from context import DatabaseInterface
import shutil

class DataStoragePathTest(unittest.TestCase):
    def test_00_instantiate(self):
        path = './test.db'
        lock = multiprocessing.Lock()
        db = DatabaseInterface(path, lock)
        
    def test_01_createFromScratch(self):
        path = './test.db'
        try:
            shutil.move(path, path + '.bak')
        except FileNotFoundError:
            pass
        
        lock = multiprocessing.Lock()
        db = DatabaseInterface(path, lock, create_new_database = True)
        
    def test_02_addNodesWithNodeName(self):
        show = False
        if show: print('  test_02_addNodes')
        expNodesTuples = (
            (0, 0, None, None, None, None),
            (1, 1, 'farm', 1, 0, None),
            (2, 2, 'horse', 1, 0, None),
            (3, 2, 'pig', 1, 1, None),
            (4, 2, 'dog', 1, 2, None),
        )
        expPreNodesTuples = (
            (0, 0, None, None, None, None, None),
            (1, 1, None, None, None, None, None),
            (2, 2, 1, 1, 1, None, None),
            (3, 2, 1, 1, 1, None, None),
            (4, 2, 1, 1, 1, None, None),
        )
        expCategoriesTuples = (
            (0, None, None),
            (1, 1, 'animals')
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = DatabaseInterface(path, lock)
        category = 'animals'
        nodes = ('horse', 'pig', 'dog')
        preNode = 'farm'
        db.addNodes((preNode,), None, None)
        db.addNodes(nodes, category_name = category, pre_node_name = preNode)
        actNodesTuples = db.dumpTable('nodes')
        self.compareTuples('nodes', expNodesTuples, actNodesTuples, show)

        actPreNodesTuples = db.dumpTable('preNodes')
        self.compareTuples('preNodes', expPreNodesTuples, actPreNodesTuples, show)

        actCategoriesTuples = db.dumpTable('categories')
        self.compareTuples('categories', expCategoriesTuples, actCategoriesTuples, show)
        
    def test_03_getNodeIds(self):
        show = False
        if show: print('  test_03_getNodeIds')
        path = './test.db'
        lock = multiprocessing.Lock()
        db = DatabaseInterface(path, lock)
        expNodeId = (2,)
        actNodeId = db.getNodeIds('horse')
        if show:
            print('    horse nodeId, exp:', expNodeId, ', act', actNodeId, end=' ')
            if expNodeId != actNodeId:
                print('********************************* ERROR ****************************')
            else: print()
        else:
            self.assertEqual(expNodeId, actNodeId)

    def test_04_addNodesWithNodeId(self):
        show = False
        if show: print('  test_04_addNodesWithNodeId')
        expNodesTuples = (
            (0, 0, None, None, None, None),
            (1, 1, 'farm', 1, 0, None),
            (2, 2, 'horse', 1, 0, None),
            (3, 2, 'pig', 1, 1, None),
            (4, 2, 'dog', 1, 2, None),
            (5, 3, 'Quarter horse', 1, 0, None),
            (6, 3, 'Mustang', 1, 1, None),
            (7, 3, 'Appaloosa', 1, 2, None),
            (8, 3, 'Morgan horse', 1, 3, None),
        )
        expPreNodesTuples = (
            (0, 0, None, None, None, None, None),
            (1, 1, None, None, None, None, None),
            (2, 2, 1, 1, 1, None, None),
            (3, 2, 1, 1, 1, None, None),
            (4, 2, 1, 1, 1, None, None),
            (5, 3, 2, 2, 2, None, None),
            (6, 3, 2, 2, 2, None, None),
            (7, 3, 2, 2, 2, None, None),
            (8, 3, 2, 2, 2, None, None),
        )
        expCategoriesTuples = (
            (0, None, None),
            (1, 1, 'animals'),
            (2, 2, 'Horse Breeds'),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = DatabaseInterface(path, lock)
        nodeId = db.getNodeIds('horse')[0]
        category = 'Horse Breeds'
        nodes = ('Quarter horse', 'Mustang', 'Appaloosa', 'Morgan horse')
        preNodeId = nodeId
        db.addNodes(nodes, category, pre_node_id = preNodeId)
        actNodesTuples = db.dumpTable('nodes')
        self.compareTuples('nodes', expNodesTuples, actNodesTuples, show)

        actPreNodesTuples = db.dumpTable('preNodes')
        self.compareTuples('nodes', expPreNodesTuples, actPreNodesTuples, show)

    def test_05_addNodesToCategory(self):
        show = False
        if show: print('  test_05_addNodesToCategory')
        expNodesTuples = (
            (0, 0, None, None, None, None),
            (1, 1, 'farm', 1, 0, None),
            (2, 2, 'horse', 1, 0, None),
            (3, 2, 'pig', 1, 1, None),
            (4, 2, 'dog', 1, 2, None),
            (5, 3, 'Quarter horse', 1, 0, None),
            (6, 3, 'Mustang', 1, 1, None),
            (7, 3, 'Appaloosa', 1, 2, None),
            (8, 3, 'Morgan horse', 1, 3, None),
            (9, 4, 'sheep', 1, 0, None),
        )
        expPreNodesTuples = (
            (0, 0, None, None, None, None, None),
            (1, 1, None, None, None, None, None),
            (2, 2, 1, 1, 1, None, None),
            (3, 2, 1, 1, 1, None, None),
            (4, 2, 1, 1, 1, None, None),
            (5, 3, 2, 2, 2, None, None),
            (6, 3, 2, 2, 2, None, None),
            (7, 3, 2, 2, 2, None, None),
            (8, 3, 2, 2, 2, None, None),
            (9, 4, 1, 1, 1, None, None)
        )
        expCategoriesTuples = (
            (0, None, None),
            (1, 1, 'animals'),
            (2, 2, 'Horse Breeds'),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = DatabaseInterface(path, lock)
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
        
    def test_06_getNodeInfo(self):
        show = True
        if show: print('  test_06_getNodeInfo')
        expNodeInfo = (
            ('dog', ((4, 'dog', 1, 'animals', None, 1, 'farm'),)),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = DatabaseInterface(path, lock)

        for (nodeName, expNodeInfo) in expNodeInfo:
            actNodeInfo = db.getNodeInfo(nodeName)
            if show:
                print('  expNodeInfo', expNodeInfo)
                print('  actNodeInfo', actNodeInfo)
                
    def compareTuples(self, tuplesName, expTuples, actTuples, show):
        if show:
            print('  ', tuplesName,':', end=' ')
            if expTuples != actTuples:
                print('******************************** ERROR ****************************')
            else: print()
            for actTuple in actTuples:
                print('     ', actTuple)
        else:
            self.assertEqual(expTuples, actTuples)
        
if __name__ == '__main__':
    unittest.main()
