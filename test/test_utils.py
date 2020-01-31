
class TestUtils:
    def _addExpDataa(self, name, dataa):
        for data in dataa:
            dataIdx = data[0]
            if dataIdx < len(self.expDataa[name]) and self.expDataa[name][dataIdx][-1] == 1:
                # the Categorizer will mark old data's validForLatest to 0
                # data must always be sent to this method in the order of old data, then
                # new data, i.e. validForLatest == 0 data first, then validForLatest == 1 data
                self.expDataa[name][dataIdx] = data
            else:
                self.expDataa[name].append(data)

    def _addExpDataaOLD(self, name, dataa):
        for data in dataa:
            dataIdx = data[0]
            if dataIdx < len(self.expDataa[name]):
                self.expDataa[name][dataIdx] = data
            else:
                self.expDataa[name].append(data)

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

    def showTables(self, db, tables):
        for tableName in tables:
            print(' ', tableName)
            for row in db.dumpTable(tableName):
                print('   ', row)
