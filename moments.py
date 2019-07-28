from music21.analysis import segmentByRests
from music21 import bar
from music21 import common
from music21 import corpus
from music21 import converter
from music21 import clef
from music21 import interval
from music21 import note
from music21 import stream

import csv
import os
import pickle
import unittest

from fractions import Fraction

# ------------------------------------------------------------------------------

def getIntervalList(elementList):
    '''
    Given a list of notes (e.g. a segment from getSegmentsList),
    returns a list of intervals between adjacent notes.
    '''

    intervalList = []

    for i in range(len(elementList)-1):
        n1 = elementList[i]
        n2 = elementList[i + 1]
        intervalObj = interval.Interval(n1, n2)
        intervalList.append(intervalObj.name)

    return intervalList

def getInfo(segmentList, startEnd=True, intervals=True, durations=True, metricalPositions=True):
    '''
    Given a list of notes (e.g. a segment from getSegmentsList),
    returns starting/ending positions for the segment and
    lists of intervals, durations, and metrical positions used (all optional).
    '''

    outInfo = []  # Macro list of dicts (one dict for each segment)

    for segment in segmentList:
        thisSegment = {}
        if startEnd==True:
            firstNote = segment[0]
            thisSegment['startingMeasure'] = firstNote.measureNumber
            thisSegment['startingOffset'] = firstNote.offset
            lastNote = segment[-1]
            thisSegment['endingMeasure'] = lastNote.measureNumber
            thisSegment['endingOffset'] = lastNote.offset + lastNote.quarterLength
        if intervals==True:
            allIntervals = getIntervalList(segment)
            thisSegment['intervals'] = set(allIntervals)
        if durations==True:
            noteValues = [x.quarterLength for x in segment]
            thisSegment['noteValues'] = set(noteValues)
        if metricalPositions==True:
            positions = [x.offset for x in segment]
            thisSegment['metricalPositions'] = set(positions)

        outInfo.append(thisSegment)

    return outInfo

def getSegmentsOfType(data, measureAvoid=[100,110], offsetAvoid=[1000,2000],
                        intvsToAvoid=['m6', 'M6'], noteValsToAvoid=[0.25, 0.125],
                        metricalPositionsToAvoid=[Fraction(7, 3)]):
    '''
    Given data of the type output by getInfo, retrieve cases matching specific requirements
    (avoiding specific measure ranges, intervals, etc.).
    Returns a list of dicts with full data for relevant cases.
    NB:
    measureAvoid and offsetAvoid = [start, end], or None
    intvsToAvoid, noteValsToAvoid, and metricalPositionsToAvoid all lists (can be empty, '[]').
    '''

    cases = []

    for segment in data:

        if measureAvoid:
            if segment['startingMeasure'] in [x for x in range(measureAvoid[0], measureAvoid[1])]:
                continue
            elif segment['endingMeasure'] in [x for x in range(measureAvoid[0], measureAvoid[1])]:
                continue
            else:
                cases.append(segment)

        elif offsetAvoid:
            if segment['startingOffset'] in [x for x in range(offsetAvoid[0], offsetAvoid[1])]:
                continue
            elif segment['endingOffset'] in [x for x in range(offsetAvoid[0], offsetAvoid[1])]:
                continue
            else:
                cases.append(segment)

        elif intvsToAvoid:
            if any(intv in segment['intervals'] for intv in intvsToAvoid):
                continue
            else:
                cases.append(segment)

        elif noteValsToAvoid:
            if any(noteValue in segment['noteValues'] for noteValue in noteValsToAvoid):
                continue
            else:
                cases.append(segment)

        elif metricalPositionsToAvoid:
            if any(metricalPosition in segment['metricalPositions'] for metricalPosition in metricalPositionsToAvoid):
                continue
            else:
                cases.append(segment)

        else:
            cases.append(segment)

    return cases

# ------------------------------------------------------------------------------

def makeCSVFile(data, csvFilePath, csvFileName):
    '''
    Makes a CSV file for one work from an input score.
    '''

    with open(csvFilePath+csvFileName, 'a') as csvfile:
        csvOut = csv.writer(csvfile, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)

        csvOut.writerow([x for x in data[0].keys()])

        for segmentData in data:
            csvOut.writerow([x for x in segmentData.values()])

def getSegmentsOfTypeCSV(csvFilePath, csvFileName,
                        intvsToAvoid=['m6', 'M6'], noteValsToAvoid=['0.25', '0.125']):
    '''
    Given data of the type output by getInfo, retrieve cases matching specific requirements
    e.g. avoiding specific intervals.
    Returns a dict with full data for relevant cases.
    '''

    cases = []

    f = open(csvFilePath+csvFileName)
    next(f)
    for row in csv.reader(f):
        if any(intv in row[2] for intv in intvsToAvoid):
            continue
        elif any(noteValue in row[3] for noteValue in noteValsToAvoid):
            continue
        else:
            cases.append(segment)

    return cases

# ------------------------------------------------------------------------------

def getFiles(path, extension=None):
    fileList = []
    for file in os.listdir(path):
        if extension:
            if file.endswith(extension):
                fileList.append(file)
        else:
            fileList.append(file)
    return fileList

def storePickle(obj, path, filename):
    filename = path + filename + '.p'
    with open(filename, 'wb') as fileout:
        pickle.dump(obj, fileout)
    return filename

def loadPickle(path, filename):
    filename = path + filename + '.p'
    with open(filename, 'rb') as filein:
        obj = pickle.load(filein)
    return obj

# ------------------------------------------------------------------------------

def makeCorpus(fileList, fileSourcePath, fileDestinationPath, update=True):
    for fileName in fileList:
        try:
            score = converter.parse(fileSourcePath+fileName)
        except:
            continue
        topLine = score.parts[0]
        segmented = analysis.segmentByRests.Segmenter.getSegmentsList(topLine)
        data = getInfo(segmented)
        storePickle(data, fileDestinationPath, fileName[:-4])
        if update==True:
            print(fileName)

def searchCorpus(directory, updates=True):
    corpusCases = []
    fileList = getFiles(directory)
    for fileName in fileList:
        if updates==True:
            print(fileName)
        if fileName.endswith('.p'):
            loadedData = loadPickle(directory, fileName[:-2])
            thisCase = getSegmentsOfType(loadedData)
            corpusCases.append([x for x in thisCase])
    return corpusCases

# ------------------------------------------------------------------------------

def renderExample(segmentData, fileSourcePath, fileName):
    '''
    Re-renders a musical fragment identified by the search,
    filing the incomplete starting and ending measures with rests as necessary with 'fillMeasures'.
    '''

    score = converter.parse(fileSourcePath+fileName)
    fragment = score.parts[0].measures(segmentData['startingMeasure'], segmentData['endingMeasure'])
    # TODO: make part choice settable (i.e. not just for lieder)

    filledFragment = fillMeasures(fragment,
                                  firstMeasureRef=segmentData['startingMeasure'],
                                  lastMeasureRef=segmentData['endingMeasure'],
                                  startOffset=segmentData['startingOffset'],
                                  endOffset=segmentData['endingOffset'])

    return filledFragment

def fillMeasures(fragment, firstMeasureRef=1, lastMeasureRef=-1, startOffset=1, endOffset=3):
    '''
    Fill out the measures at the start / end of a musical fragment to ensure readabiltiy in various softwares.
    '''

    # Measure refs. 1:-1 by default (all called), or actual measure number (when referencing original score)
    firstMeasure = fragment.measure(firstMeasureRef)
    lastMeasure = fragment.measure(lastMeasureRef)
    measureLength = firstMeasure.quarterLength

    startRest = note.Rest()
    startRest.quarterLength = startOffset
    for x in firstMeasure.recurse().notesAndRests:
        if x.offset < startOffset:
            fragment.remove(x, recurse=True)
        else:
            continue  # Exit loop once reached the position after
    firstMeasure.insert(0, startRest)

    endRest = note.Rest()
    endRest.quarterLength = measureLength - endOffset
    for x in lastMeasure.recurse().notesAndRests[::-1]:
        if x.offset >= endOffset:
            fragment.remove(x, recurse=True)
        else:
            continue
    lastMeasure.insert(endOffset, endRest)

    return fragment

# ------------------------------------------------------------------------------

class Test(unittest.TestCase):

    testScore = corpus.parse('schubert/Lindenbaum')
    testFragment = testScore.measures(0,20).parts[0]
    segments = segmentByRests.Segmenter.getSegmentsList(testFragment)
    info = getInfo(segments)

    def preTest(self):
        self.assertIsInstance(segments[0], list)
        self.assertEqual(segments[0][0].name, 'B')

    def testGetIntervalList(self):

        intvEgs = getIntervalList(segments[0])
        # ['P1', 'm3', 'P1', 'P1', 'P1', 'M3']

        self.assertIsInstance(intvEgs, list)
        self.assertEqual(len(intvEgs), 6)
        self.assertEqual(intvEgs[0], 'P1')

    def testGetInfo(self):

        oneInfoSet = info[0]

        self.assertIsInstance(oneInfoSet, dict)
        self.assertEqual(oneInfoSet['endingMeasure'], 10)
        self.assertEqual(len(oneInfoSet['intervals']), 3)

    def testGetSegmentsOfType(self):

        filteredData = getSegmentsOfType(info, measureAvoid=None, offsetAvoid=None,
                                            intvsToAvoid=['m6', 'M6'], noteValsToAvoid=['0.25', '0.125'],
                                            metricalPositionsToAvoid=[Fraction(7, 3)])

        oneInfoSet = filteredData[0]

        self.assertIsInstance(filteredData, list)
        self.assertIsInstance(oneInfoSet, dict)
        self.assertEqual(oneInfoSet['endingMeasure'], 10)
        self.assertEqual(len(oneInfoSet['intervals']), 3)

    ## TODO: More tests:

    # def testMakeCSVFile(self):
    #     self.assertIsInstance()
    #     self.assertEqual(
    # def testGetSegmentsOfTypeCSV(self):
    #     self.assertIsInstance()
    #     self.assertEqual()
    # def testGetFiles(self):
    #     self.assertIsInstance()
    #     self.assertEqual()
    # def testStorePickle(self):
    #     self.assertIsInstance()
    #     self.assertEqual()
    # def testLoadPickle(self):
    #     self.assertIsInstance()
    #     self.assertEqual()
    # def testMakeCorpus(self):
    #     self.assertIsInstance()
    #     self.assertEqual()
    # def testSearchCorpus(self):
    #     self.assertIsInstance()
    #     self.assertEqual()
    # def testRenderExample(self):
    #     self.assertIsInstance()
    #     self.assertEqual()
    # def testFillMeasures(self):
    #     self.assertIsInstance()
    #     self.assertEqual()

# -------------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
