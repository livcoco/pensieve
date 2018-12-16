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
        shutil.move(path, path + '.bak')
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
            (0, 0, None, None, None, None),
            (1, 1, None, None, None, 'farm'),
            (2, 2, 1, 1, 'animals', 'horse'),
            (3, 2, 1, 1, 'animals', 'pig'),
            (4, 2, 1, 1, 'animals', 'dog'),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = DatabaseInterface(path, lock)
        category = 'animals'
        nodes = ('horse', 'pig', 'dog')
        preNode = 'farm'
        db.addNodes((preNode,), None, None)
        db.addNodes(nodes, category, preNode)
        nodesTuples = db.dumpTable('nodes')
        if show:
            print('    nodesTuples:', end=' ')
            if expNodesTuples != nodesTuples:
                print('******************************** ERROR ****************************')
            else: print()
            for nodesTuple in nodesTuples:
                print('     ', nodesTuple)
        else:
            self.assertEqual(expNodesTuples, nodesTuples)
        preNodesTuples = db.dumpTable('preNodes')
        if show:
            print('    preNodesTuples:', end=' ')
            if expPreNodesTuples != preNodesTuples:
                print('******************************** ERROR ****************************')
            else: print()
            for preNodesTuple in preNodesTuples:
                print('     ', preNodesTuple)
        else:
            self.assertEqual(expPreNodesTuples, preNodesTuples)
            
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
            (0, 0, None, None, None, None),
            (1, 1, None, None, None, 'farm'),
            (2, 2, 1, 1, 'animals', 'horse'),
            (3, 2, 1, 1, 'animals', 'pig'),
            (4, 2, 1, 1, 'animals', 'dog'),
            (5, 3, 2, 2, 'Horse Breeds', 'Quarter horse'),
            (6, 3, 2, 2, 'Horse Breeds', 'Mustang'),
            (7, 3, 2, 2, 'Horse Breeds', 'Appaloosa'),
            (8, 3, 2, 2, 'Horse Breeds', 'Morgan horse'),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = DatabaseInterface(path, lock)
        nodeId = db.getNodeIds('horse')[0]
        category = 'Horse Breeds'
        nodes = ('Quarter horse', 'Mustang', 'Appaloosa', 'Morgan horse')
        preNodeId = nodeId
        db.addNodes(nodes, category, pre_node_id = preNodeId)
        nodesTuples = db.dumpTable('nodes')
        if show:
            print('    nodesTuples:', end=' ')
            if expNodesTuples != nodesTuples:
                print('******************************** ERROR ****************************')
            else: print()
            for nodesTuple in nodesTuples:
                print('     ', nodesTuple)
        else:
            self.assertEqual(expNodesTuples, nodesTuples)
        preNodesTuples = db.dumpTable('preNodes')
        if show:
            print('    preNodesTuples:', end=' ')
            if expPreNodesTuples != preNodesTuples:
                print('******************************** ERROR ****************************')
            else: print()
            for preNodesTuple in preNodesTuples:
                print('     ', preNodesTuple)
        else:
            self.assertEqual(expPreNodesTuples, preNodesTuples)

if __name__ == '__main__':
    unittest.main()
