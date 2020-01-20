'''
history
12/19/18 - 
    add try for test01, 
    r'SELECT... == "{}"'.format(catname)
    change to try: instead of return False

'''
import unittest
import multiprocessing
from context import CategorizerData, CategorizerLanguage
import shutil
import fuzzy

# create global expect data.
# start with the default values as defined in the class
# as test are run, things are added and changed in the database,
# and things are added and changed to the expect dataa
EXPDATAA = {
    'categories'    : [CategorizerData.tableInits['categories']],
    'catVariants'   : [CategorizerData.tableInits['catVariants']],
    'catNodes'      : [CategorizerData.tableInits['catNodes']],
    'relations'     : [CategorizerData.tableInits['relations']],
    'relVariants'   : [CategorizerData.tableInits['relVariants']],
    'catConnections': [CategorizerData.tableInits['catConnections']],
    'nodeStyles'    : [CategorizerData.tableInits['nodeStyles']],
    'fonts'         : [CategorizerData.tableInits['fonts']],
}
class DataStoragePathTest(unittest.TestCase):
    runAll = True
    runTestCounts = list(range(3))
    fontSet = CategorizerLanguage.FontSet
    
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
        addCats = ('Farm', 'Horse', 'Pig', 'Dog')
        newExpCats = (
            #catId, pathRev, catName, dMetaName0, dMetaName1, validForLatest
            (1, 1,  'Farm', 'FRM', '', 1),
            (2, 1, 'Horse', 'HRS', '', 1),
            (3, 1,   'Pig', 'PK', '', 1),
            (4, 1,   'Dog', 'TK', '', 1),
        )
        newExpCatVars = (
            #catVarId, pathRev, catId, catVarName, dMetaName0, dMetaName1, validForLatest
            (1, 1, 1,   None, '', '', 1),
            (2, 1, 2,   None, '', '', 1),
            (3, 1, 3,   None, '', '', 1),
            (4, 1, 4,   None, '', '', 1),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        dMeta = fuzzy.DMetaphone()
        for idx, cat in enumerate(addCats):
            db._addCategory(cat)
        self._addExpDataa('categories', newExpCats)
        self._addExpDataa('catVariants', newExpCatVars)
        actCats = db.dumpTable('categories')
        self.compareTuples('categories', EXPDATAA['categories'], actCats, show)
        actCatVars = db.dumpTable('catVariants')
        self.compareTuples('catVariants', EXPDATAA['catVariants'], actCatVars, show)

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
        newExpCatVars = (
            #skip variant for Farm
            (5, 1, 2,  'horsey', 'HRS', '', 1),
            (6, 1, 3,   'piggy', 'PK', '',  1),
            (7, 1, 4,  'doggie', 'TJ', 'TK',  1),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for i in range(len(addCatVars)):
            catId = addCatVars[i][2]
            catVarName = addCatVars[i][3]
            db._addCatVariant(catId, catVarName)
        self._addExpDataa('catVariants', newExpCatVars)
        actCats = db.dumpTable('categories')
        self.compareTuples('categories', EXPDATAA['categories'], actCats, show)
        actCatVars = db.dumpTable('catVariants')
        self.compareTuples('catVariants', EXPDATAA['catVariants'], actCatVars, show)

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
        newExpCatNodes = (
            #catNodeId, pathRev, catVarId, dx, dy, nodeStyleId, validForLatest
#            (0, 0, 0,  None, None, 0, 0),
            (1, 1, 1,  None, None, None, 0, 1),
            (2, 1, 2,  None, None, None, 0, 1),
            (3, 1, 5,  None, None, None, 0, 1),
            (4, 1, 6,  None, None, None, 0, 1),
            (5, 1, 8,  None, None, None, 0, 1),
            (6, 1, 9,  None, None, None, 0, 1),
        )
        newExpCats = (
            #catId, pathRev, catName, validForLatest
            (5, 1,   'cow', 'K', 'KF',1),
            (6, 1,   'sheep', 'XP', '', 1),
        )
        newExpCatVars = (
            #catVarId, pathRev, catId, catName, validForLatest
            (8, 1, 5,  None, '', '', 1),
            (9, 1, 6,  None, '', '', 1),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for i in range(len(addCatNodes)):
            catVarId = addCatNodes[i][0]
            catVarName = addCatNodes[i][1]
            db.addCatNode(catVarId, catVarName)
        self._addExpDataa('categories', newExpCats)
        self._addExpDataa('catVariants', newExpCatVars)
        self._addExpDataa('catNodes', newExpCatNodes)
        
        actCats = db.dumpTable('categories')
        self.compareTuples('categories', EXPDATAA['categories'], actCats, show)
        actCatVars = db.dumpTable('catVariants')
        self.compareTuples('catVariants', EXPDATAA['catVariants'], actCatVars, show)
        actCatNodes = db.dumpTable('catNodes')
        self.compareTuples('catNodes', EXPDATAA['catNodes'], actCatNodes, show)

    def test_05_addRelation(self):
        if not self.runAll:
            if 5 not in self.runTestCounts:
                return
        show = False
        print('  test_05_addRelation')
        addRels = (
            #prefix, relName, validForLatest
            ('hyper', 'is-a', 'out'),
            ('super', 'has-a', 'in'),
            ('pre', 'prior in sequence', 'out'),
            ('pre', 'prior in cycle', 'out'),
        )
        expRels = (
            #relId*, pathRev*, prefix, relName, dMetaName0, dMetaName1, direction, validForLatest
            (1, 1, 'hyper', 'is-a', 'AS', '', 'out', 1),
            (2, 1, 'super', 'has-a', 'HS', '', 'in', 1),
            (3, 1, 'pre', 'prior in sequence', 'PRRN', '', 'out',1),
            (4, 1, 'pre', 'prior in cycle', 'PRRN', '', 'out', 1),
        )
        expRelVars = (
            #relVarId*, pathRev*, relId, relVarPrefix, relVarName, varDirection, validForLatest
            (1, 1, 1,   None, None, '', '', None, 1),
            (2, 1, 2,   None, None, '', '', None, 1),
            (3, 1, 3,   None, None, '', '', None, 1),
            (4, 1, 4,   None, None, '', '', None, 1),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for (relPrefix, relName, direction) in addRels:
            db._addRelation(relPrefix, relName, direction)
        self._addExpDataa('relations', expRels)
        self._addExpDataa('relVariants', expRelVars)
        actRels = db.dumpTable('relations')
        self.compareTuples('relations', EXPDATAA['relations'], actRels, show)
        actRelVars = db.dumpTable('relVariants')
        self.compareTuples('relVariants', EXPDATAA['relVariants'], actRelVars, show)

    def test_06_addRelationVariant(self):
        if not self.runAll:
            if 6 not in self.runTestCounts:
                return
        show = False
        print('  test_06_addRelationVariant')
        addRelVars = (
            #relId, relVarPrefix, relVarName, varDirection
            (2, None, 'reverse has-a', 'out'),
            (3, 'prePIS', 'PIS', None),
            (4, 'prePIC', 'PIC', None),
        )
        newExpRelVars = (
            #relVarId, pathRev, relId, relVarPrefix, relVarName, varDirection, validForLatest
            (5, 1, 2, None, 'reverse has-a', 'RFRS', '', 'out', 1), #new relation variant for relId 2 with new direction
            (6, 1, 3, 'prePIS', 'PIS', 'PS', '', None, 1), #new relation variant for relId 3
            (7, 1, 4, 'prePIC', 'PIC', 'PK', '', None, 1), #new relation variant for relId 4
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for (relId, relVarPrefix, relVarName, direction) in addRelVars:
            db._addRelVariant(relId, relVarPrefix, relVarName, direction)
        self._addExpDataa('relVariants', newExpRelVars)
        actRelVars = db.dumpTable('relVariants')
        self.compareTuples('relVariants', EXPDATAA['relVariants'], actRelVars, show)

    def test_07_addConnection(self):
        '''
        add a connection between catNodes
        find the relation for the connection if it exists
        make a new relation if it does not exist.
        '''
        if not self.runAll:
            if 7 not in self.runTestCounts:
                return
        show = False
        print('  test_07_addConnection')
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        addConns = (
            #catNodeId, superCatNodeId, relVarId, connStyleId
            (4, 3, 3, None), #1 create a connection from relVarId 3, i.e. 
            (4, 3, 0, None), #2 just make an unspecified connection, (default relationVariant)
            (4, 3, None, 'reverse has-a'), #3 make a connection based on an existing relVarName
            (4, 3, None, 'is-a'), #4 make a connection based on an existing relation Name
            (4, 3, None, 'from'), #5 make a connection based on a new relation Name
            )
        newExpCatConns = (
            #catConnId, pathRev, catNodeId, superCatNodeId, relVarId, connStyleId validForLatest
            (1, 1, 4, 3, 3, 0, 1),
            (2, 1, 4, 3, 0, 0, 1),
            (3, 1, 4, 3, 5, 0, 1),
            (4, 1, 4, 3, 1, 0, 1),
            (5, 1, 4, 3, 8, 0, 1),
        )
        for (catNodeId, superCatNodeId, relVarId, relVarName) in addConns:
            #                from       to              use one of these or neither
            db.addConnection(catNodeId, superCatNodeId, relVarId, relVarName)
        self._addExpDataa('catConnections', newExpCatConns)
        
        actCatConns = db.dumpTable('catConnections')
        self.compareTuples('catConnections', EXPDATAA['catConnections'], actCatConns, show)

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
        show = False
        print('  test_08_editCatNode')
        editCatNodes = (
            #catNodeId, newCatVarId, newDx, newDy, newDz
            (1, 2, None, None, None, None), #change from 1: 'Farm' to 2: 'Horse'
            (2, 5, None, None, None, None), #change from 2: 'Horse' to 5: 'Horsey'
            (3, 5, None, 22, None, None), # change dx to 22
            (4, 6, None, None, None, 37), # change dy to 37
            (5, 6, None, 11, 15, 4), # change catVarId 6, dx to 11, dy 15
            (6, None, 'Bird', 9, 7, 5), # add new catVarName 'Bird', change dx to 9, dy 7
        )
        newExpCatNodes = (
            #catNodeId, pathRev, catVarId, dx, dy, dz, validForLatest
            (1, 1, 2,  None, None, None, 0, 1), # catVarId to '2'
            (2, 1, 5,  None, None, None, 0, 1), # catVarId to '5'
            (3, 1, 5,  22, None, None, 0, 1), # dx to 22
            (4, 1, 6,  None, None, 37, 0, 1), # dz to 37
            (5, 1, 6,  11, 15, 4, 0, 1), # catVarId 6, dx 11, dy 15, dz 4
            (6, 1, 10,  9, 7, 5, 0, 1),
        )
        newExpCats = (
            #catId, pathRev, catName, validForLatest
            (7, 1,   'Bird', 'PRT', '', 1),
        )
        newExpCatVars = (
            #catVarId, pathRev, catId, catName, validForLatest
            (10, 1, 7,  None, '', '', 1),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for (catNodeId, newCatVarId, newCatVarName, newDx, newDy, newDz) in editCatNodes:
            db.editCatNode(catNodeId, newCatVarId, newCatVarName, newDx, newDy, newDz)
        self._addExpDataa('categories', newExpCats)
        self._addExpDataa('catVariants', newExpCatVars)
        self._addExpDataa('catNodes', newExpCatNodes)
        actCatNodes = db.dumpTable('catNodes')
        self.compareTuples('catNodes', EXPDATAA['catNodes'], actCatNodes, show)
        actCats = db.dumpTable('categories')
        self.compareTuples('categories', EXPDATAA['categories'], actCats, show)
        actCatVars = db.dumpTable('catVariants')
        self.compareTuples('catVariants', EXPDATAA['catVariants'], actCatVars, show)

    def test_09_editCategory(self):
        if not self.runAll:
            if 9 not in self.runTestCounts:
                return
        show = False
        print('  test_09_editCategory')
        edits = (
            #cat_id, cat_name
            (2, 'Horses'),
            (3, 'Pigs'),
            (4, 'Dogs'),
            (5, 'Cows'),
            (6, 'Sheep'),
            (7, 'Fowl'),
        )
        newExpCats = (
            #catId, pathRev, catName, validForLatest
            (2, 1, 'Horses', 'HRSS', '', 1),
            (3, 1,   'Pigs', 'PKS', '', 1),
            (4, 1,   'Dogs', 'TKS', '', 1),
            (5, 1,   'Cows', 'KS', '', 1),
            (6, 1,  'Sheep', 'XP', '', 1),
            (7, 1,   'Fowl', 'FL', '', 1),
        )
        newExpCatVars = (
            #catVarId, pathRev, catId, catName, validForLatest
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for i in range(len(edits)):
            catId = edits[i][0]
            catName = edits[i][1]
            db.editCategory(catId, catName)
        self._addExpDataa('categories', newExpCats)
        self._addExpDataa('catVariants', newExpCatVars)
        actCats = db.dumpTable('categories')
        self.compareTuples('categories', EXPDATAA['categories'], actCats, show)
        actCatVars = db.dumpTable('catVariants')
        self.compareTuples('catVariants', EXPDATAA['catVariants'], actCatVars, show)

    def test_10_editCatVariant(self):
        if not self.runAll:
            if 10 not in self.runTestCounts:
                return
        show = False
        print('  test_10_editCatVariant')
        edits = (
            #cat_var_id, cat_var_name
            (5, 'horseee'),
            (6, 'oink oink'),
            (7, 'woof dog'),
        )
        newExpCats = (
            #catId, pathRev, catName, dMetaName0, dMetaName1, validForLatest
        )
        newExpCatVars = (
            #catVarId, pathRev, catId, catName, dMetaName0, dMetaName1, validForLatest
            (5, 1, 2,  'horseee', 'HRS', '', 1),
            (6, 1, 3,   'oink oink', 'ANKN', '', 1),
            (7, 1, 4,  'woof dog', 'AFTK', 'FFTK', 1),
        )
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        for i in range(len(edits)):
            catVarId = edits[i][0]
            catVarName = edits[i][1]
            db.editCatVariant(catVarId, catVarName)

        self._addExpDataa('catVariants', newExpCatVars)
        self._addExpDataa('categories', newExpCats)
        actCats = db.dumpTable('categories')
        self.compareTuples('categories', EXPDATAA['categories'], actCats, show)
        actCatVars = db.dumpTable('catVariants')
        self.compareTuples('catVariants', EXPDATAA['catVariants'], actCatVars, show)

    def test_11_editConnection(self):
        '''
        edit a connection between catNodes
        find the relation for the connection if it exists
        make a new relation if it does not exist.
        '''
        if not self.runAll:
            if 11 not in self.runTestCounts:
                return
        show = False
        print('  test_11_editConnection')
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        editConns = (
            #catConnId, catNodeId, superCatNodeId, relVarId, relVarName, connStyleId
            (2, 3, 4, None, None, None), #reverse the connection
            (3, None, None, 1, None, None), #change the relation using a relVarId
            (5, None, None, None, 'reverse has-a', None), # change the relation using a relVarName
            )
        newExpCatConns = (
            #catConnId, pathRev, catNodeId, superCatNodeId, relVarId, connStyleId validForLatest
            (2, 1, 3, 4, 0, 0, 1),
            (3, 1, 4, 3, 1, 0, 1),
            (5, 1, 4, 3, 5, 0, 1),
        )
        for (catConnId, catNodeId, superCatNodeId, relVarId, relVarName, connStyleId) in editConns:
            #                from       to              use one of these or neither
            db.editConnection(catConnId, catNodeId, superCatNodeId, relVarId, relVarName, connStyleId)
        self._addExpDataa('catConnections', newExpCatConns)
        
        actCatConns = db.dumpTable('catConnections')
        self.compareTuples('catConnections', EXPDATAA['catConnections'], actCatConns, show)

    def test_12_addNodeStyle(self):
        '''
        '''
        if not self.runAll:
            if 12 not in self.runTestCounts:
                return
        show = False
        print('  test_12_addNodeStyle')
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        addNodeStyles = (
            #styleName, fontId, fontfamily, fontStyle, fontSize, fontColor, backgroundColor, transparency
            ('typical'   , None,      None,   None, None,    None, None, None),
            ('bigNBold'  , None, 'Verdana', 'bold',   16, 'Black', None, None), #make new font
            ('seeThroughRed', None,   None,   None, None,    None, 'Red', 50),
            ('blueBigNBold', None,'Verdana', 'bold',   16, 'Black', 'Blue', 30), #get exising font from description
            ('plainBold', 1,   None,   None, None,    None, 'Black', None), #use existing font by fontId
            )
        newNodeStyles = (
            #nodeStyleId, pathRev, styleName, dMetaName0, dMetaName1, fontId, backgorundCXolor, transparency, validForLatest
            (1, 1, 'typical', 'TPKL', '', 0, None, None, 1),
            (2, 1, 'bigNBold', 'PNPL', 'PKNP', 1, None, None, 1),
            (3, 1, 'seeThroughRed', 'S0RR', 'STRR', 0, 'Red', 50, 1),
            (4, 1, 'blueBigNBold', 'PLPN', 'PLPK', 1, 'Blue', 30, 1),
            (5, 1, 'plainBold', 'PLNP', '', 1, 'Black', None, 1),
        )
        newFonts = (
            (1, 1, 'Verdana', 'bold', 16, 'Black', 1),
        )
        for (styleName, fontId, fontFamily, fontStyle, fontSize, fontColor, backgroundColor, transparency) in addNodeStyles:
            tmpFontSet = self.fontSet(fontFamily, fontStyle, fontSize, fontColor)
            #                from       to              use one of these or neither
#            db.addNodeStyle(styleName, fontId, fontFamily, fontStyle, fontSize, fontColor, backgroundColor, transparency)
            db.addNodeStyle(styleName, fontId, tmpFontSet, backgroundColor, transparency)
        self._addExpDataa('nodeStyles', newNodeStyles)
        self._addExpDataa('fonts', newFonts)
        
        actNodeStyles = db.dumpTable('nodeStyles')
        actFonts = db.dumpTable('fonts')
        self.compareTuples('nodeStyles', EXPDATAA['nodeStyles'], actNodeStyles, show)
        self.compareTuples('fonts', EXPDATAA['fonts'], actFonts, show)

    def _test_20_findCatVariants(self):
        '''
        '''
        if not self.runAll:
            if 20 not in self.runTestCounts:
                return
        show = False
        print('  test_20_findCatVariants')
        path = './test.db'
        lock = multiprocessing.Lock()
        db = CategorizerData(path, lock)
        findNames = (
            #name, onlyLatest
            ('finds nothing', True), #finds nothing
            ('pig', True),
            ('pigs', False),
        )
        expCatVarIdss = (
            (0,),
            (3,6),
            (3,6),
        )
        for (name, onlyLatest), expCatVarIds in zip(findNames, expCatVarIdss):
            actCatVarIds = db.findCatVariantIds(name, onlyLatest)
            if show:
                print('  exp:', expCatVarIds, ', act:', actCatVarIds, end='')
                if expCatVarIds != actCatVarIds:
                    print('***********************ERROR*****************************')
                else: print()
            else:
                self.assertEqual(expCatVarIds, actCatVarIds)
                
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
            self.assertEqual(tuple(expTuples), tuple(actTuples))

    def _addExpDataa(self, name, dataa):
        for data in dataa:
            dataIdx = data[0]
            if dataIdx < len(EXPDATAA[name]):
                EXPDATAA[name][dataIdx] = data
            else:
                EXPDATAA[name].append(data)
                
if __name__ == '__main__':
    unittest.main()
