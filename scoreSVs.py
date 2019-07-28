'''
About:

This file provides code for
- extracting 'slices' of chord and rest info from scores,
- writing that summative information to a separated values file,
- retreiving such information from such a separated values file, and
- working with that data.

The separated values files are modelled on 'YCAC' (White and Quinn 2014, see https://ycac.yale.edu/) but
note that this is not the code used to generate YCAC (author unaffiliated with the YCAC project).
Differences include:
- entries for rests as well as chords,
- more temporal information than YCAC could derive (due to working with MIDI):
measure, beat (metrical position), beat strength, and length.

Possible TODO:
- the option for evenly spaced slices (useful for vector representations in machine learning tasks).

To use this in public-facing projects, please acknowledge this source.
'''

from music21 import common
from music21 import pitch
from music21 import interval
from music21 import stream
from music21 import converter

from fractions import Fraction
from collections import Counter
from itertools import combinations
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
import unittest


# ------------------------------------------------------------------------------

class TableEntry(object):
    '''
    Defines the data to be retrieved stored, and assessed for each chord 'slice':

    measure = measure number in the piece overall, starting with 1, or 0 in the cases of incomplete first measures;
    beat = the beat in the measure always starting with 1 (NB not 0), whatever the time signature);
    beatStrength = a simplified metric for the 'importance' of a position in the measure;
    length = how long the slice lasts, measured in 'quarterLength' (how many quarter notes - can be a fraction);
    pitches = each pitch (with octave) in the chord, working from lowest to highest;
    intervals = the intervals between each pair of pitches in the chord;
    primeForm and normalOrder = music theoretic representations of 'distinct' chord types.
    '''

    def __init__(self):
        self.measure = None
        self.beat = None
        self.beatStrength = None
        self.length = None
        self.pitches = None
        self.intervals = None
        self.primeForm = None
        self.normalOrder = None


# ------------------------------------------------------------------------------

class ScoreInfoSV:
    '''
    Retrieve chord and rest info from scores.
    Optionally: create a variant dataset with equal, repeated slice lengths
    Optionally: exporting to a separated values file.
    '''


    def __init__(self, score):
        self.score = score
        self.svFileName = ''
        self.name()
        self.data = self.extractData()


    def name(self):
        '''
        Names the sv file based on any available metadata.
        '''

        metadata = [x[1] for x in self.score.metadata.all()]  # Values
        if metadata == []:
            self.svFileName = 'UNNAMED_SV_FILE.tsv'
        else:
            svFileName = '_'.join(metadata)
            svFileName = svFileName.replace('.mxl', '')
            svFileName = svFileName.replace('.', '-')
            svFileName = svFileName.replace(' ', '_')
            self.svFileName = svFileName+'.tsv'


    def extractData(self):
        '''
        Extracts chord and rest info from scores.
        '''

        chordScore = self.score.chordify()
        info = []

        for x in chordScore.recurse():

            if ('Rest' in x.classes) or ('Chord' in x.classes):
                # NB: Attributes in both and no 'notes' in chordify (only chords)

                thisEntry = TableEntry()

                thisEntry.measure = int(x.measureNumber)
                thisEntry.beat = round((x.beat), 2)
                thisEntry.beatStrength = x.beatStrength
                thisEntry.length = float(x.quarterLength)

                if 'Chord' in x.classes:  # Attributes in chord, but not rest
                    thisEntry.pitches = list(dict.fromkeys([p.nameWithOctave for p in x.pitches]))
                    thisEntry.intervals = getIntervals(x)
                    thisEntry.primeForm = x.primeForm
                    thisEntry.normalOrder = x.normalOrder

                info.append(thisEntry)

        return info


    def makeSV(self, svFilePath):
        '''
        Writes the separated values file (TSV rather than CSV here).
        '''

        with open(svFilePath+self.svFileName, 'w') as svfile:
            svOut = csv.writer(svfile, delimiter='\t',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)

            for entry in self.data:
                svOut.writerow([entry.measure,
                                entry.beat,
                                entry.beatStrength,
                                entry.length,
                                entry.pitches,
                                entry.intervals,
                                entry.primeForm,
                                entry.normalOrder,])


# ------------------------------------------------------------------------------

class SVInfo:
    '''
    For retrieving musical information from the SV files created by ScoreInfoSV.
    '''


    def __init__(self, svPath):
        self.svPath = svPath
        self.data = self.parseSV()


    def parseSV(self):
        '''
        Takes an SV file and returns the data.
        '''

        file = self.svPath

        f = open(file, 'r')

        data = []

        for row_num, line in enumerate(f):
            values = line.split('\t')
            thisEntry = TableEntry()
            thisEntry.measure = int(values[0])
            thisEntry.beat = float(values[1])
            thisEntry.beatStrength = float(values[2])
            thisEntry.length = float(values[3])
            thisEntry.pitches = str(values[4])
            thisEntry.intervals = str(values[5])
            thisEntry.primeForm = str(values[6])
            thisEntry.normalOrder = str(values[7][:-1])

            data.append(thisEntry)

        f.close()

        return data


    def setsOfType(self, chordType='[0, 4, 8]', weighted=False, measures=True):
        '''
        Gets all cases of a specific chord type (expressed as a PC Set) and
        returns a count (integer) of the number of occurences, or
        if weighted==True, then that usage weighted by the quarterLength of those occurences.
        If measures==True, also returns the list of measure locations.
        '''

        count = 0
        msrs = []

        for entry in self.data:
            if entry.primeForm == chordType:
                if measures == True:
                    msrs.append(entry.measure)
                if weighted == True:
                    count += entry.length
                else:
                    count += 1

        if measures == True:
            return round(count, 3), msrs
        else:
            return round(count, 3)


    def intervalsOfType(self, intervals=['A6', 'd3', 'A13', 'd10'], weighted=True, measures=True):
        '''
        Gets all entries including at least one of the given interval(s) and
        returns a count (integer) of the number of occurences, or
        if weighted==True, then that usage weighted by the quarterLength of those occurences.
        If measures==True, also returns the list of measure locations.
        Defaults to intervals=['A6', 'd3', 'A13', 'd10'] as a proxy for finding augmented 6th chords.
        (Can't be included in setsOfType as it requires enharmonic information.)
        '''

        count = 0
        msrs = []
        for entry in self.data:
            intersection = [i for i in intervals if i in entry.intervals]
            if intersection:  # I.e. if there is any intersection
                if measures == True:
                    msrs.append(entry.measure)
                if weighted == True:
                    count += entry.length
                else:
                    count += 1

        if measures == True:
            return round(count, 3), list(dict.fromkeys(msrs))
        else:
            return round(count, 3)


    def getAllPrimes(self):
        '''
        Retrieves all prime forms in a file for subsequent comparisons.
        '''

        self.primes = [entry.primeForm for entry in self.data]
        return self.primes


    def getAllNormals(self):
        '''
        Retrieves all normal orders in a file for subsequent comparisons.
        '''

        self.normals = [entry.normalOrder for entry in self.data]
        return self.normals


    def compareAllPrimes(self,
                          triadsOfInterest=('major','minor'),
                          Counts=True,
                          Proportions=True,):
        '''
        Compares relative usage of triad types in a file
        expressed in terms of counts, proportion of the whole, or both.
        Options: 'major', 'minor', 'diminished', 'augmented', 'triads' (all of the above)
        '''

        overallInfo = []

        self.getAllPrimes()
        primeList = self.primes

        total = len(primeList)

        hitList = []
        if 'major' in triadsOfInterest:
            hitList.append('[0, 4, 7]')
        if 'minor' in triadsOfInterest:
            hitList.append('[0, 3, 7]')
        if 'diminished' in triadsOfInterest:
            hitList.append('[0, 3, 6]')
        if 'augmented' in triadsOfInterest:
            hitList.append('[0, 4, 8]')
        if 'triads' in triadsOfInterest:
            hitList.append('[0, 4, 7]', '[0, 3, 7]', '[0, 3, 6]', '[0, 4, 8]')
            # TODO: generalise wider than triads; accept any prime?
        if hitList == []:
            optionsList = ['major', 'minor', 'diminished', 'augmented', 'triads']
            raise ValueError("Please chose one or more triad types: "+[x for x in optionsList])

        if Counts:
            currentTuple = ('Overall', total)
            overallInfo.append(currentTuple)
        for triad in hitList:
            currentCount = primeList.count(triad)
            if Counts:
                currentName = triad+' Count'
                currentTuple = (currentName, currentCount)
                overallInfo.append(currentTuple)
            if Proportions:
                currentName = triad+' Proportion'
                currentTuple = (currentName, currentCount/total)
                overallInfo.append(currentTuple)

        return overallInfo


    def followChord(self,
                    targetChord = '[0, 4, 8]',
                    histogram=False,
                    howMany=15,
                    ignoreFirst=False):
        '''
        Get data for the chords which follow an input target chord of interest.
        Optionally, return a histogram for the most common.
        '''

        self.getAllPrimes()
        pcs = self.primes

        # Get position info for targetChord
        positions = []
        for i in [i for i,x in enumerate(pcs) if x == targetChord]:
            positions.append(i)

        # Retrieve following chord
        following = []
        for p in positions:
            following.append(pcs[p+1])

        fullCount = Counter(following)

        if ignoreFirst==True:
            start=1
        else:
            start=0

        if len(fullCount) > howMany:
            count = fullCount.most_common()[start:howMany:1]
        else:
            count = fullCount.most_common()[start:]

        if histogram==False:
            return count
        else:
            labels, values = zip(*count)
            indexes = np.arange(len(labels))
            width = 0.5
            ##Plot
            plt.bar(indexes, values, width)
            plt.title("Chord usage",fontsize=16)
            plt.xlabel("Chord type", fontsize=12)
            plt.ylabel("Count", fontsize=12)
            plt.xticks(indexes + width*0.5, labels, rotation=90)
            plt.xticks(indexes, labels, rotation=90)
            plt.gcf().subplots_adjust(bottom=0.25)
            plt.savefig('Next.png', facecolor='w', edgecolor='w', format='png')
            return count
            return plt


# ------------------------------------------------------------------------------

# Static functions

def getIntervals(aChord):
    '''
    Return a list of interval names (strings) from a music21 chord.
    '''

    intervals = []
    pairs = combinations(aChord, 2)
    for pair in pairs:
        intv = interval.Interval(pair[0], pair[1])
        intervals.append(intv.name)

    return list(dict.fromkeys(intervals))


# ------------------------------------------------------------------------------

class Test(unittest.TestCase):


    def test_ScoreInfoSV(self, write=False):

        from music21 import corpus

        score = corpus.parse('bach/bwv269')
        info = ScoreInfoSV(score)

        self.assertIsInstance(info, ScoreInfoSV)
        self.assertIsInstance(info.data[0], TableEntry)
        self.assertEqual(info.data[0].measure, 0)

        if write:
            pathToDesktop = os.path.expanduser('~')+'/Desktop/'
            info.makeSV(pathToDesktop)


    def test_SVInfo(self):  # TODO: more tests for all options and routes

        svegfile = 'SV-EG-bwv269.tsv'

        info = SVInfo(svegfile)

        self.assertIsInstance(info, SVInfo)
        self.assertIsInstance(info.data[0], TableEntry)
        self.assertEqual(info.data[0].measure, 0)

        all0247s = info.setsOfType(chordType='[0, 2, 4, 7]', weighted=False, measures=True)
        self.assertEqual(all0247s, (4, [8, 13, 15, 17]))

        all0247sWeighted = info.setsOfType(chordType='[0, 2, 4, 7]', weighted=True, measures=True)
        self.assertEqual(all0247sWeighted, (2.0, [8, 13, 15, 17]))

        self.assertEqual(all0247s[1], all0247sWeighted[1])


        allDim5s = info.intervalsOfType(intervals=['d5'], weighted=False)
        self.assertEqual(allDim5s, (6, [5, 8, 9, 12, 15, 19]))

        allDim5sWeighted = info.intervalsOfType(intervals=['d5'], weighted=True)
        self.assertEqual(allDim5sWeighted, (4.0, [5, 8, 9, 12, 15, 19]))

        self.assertEqual(allDim5s[1], allDim5sWeighted[1])


        allAugs = info.compareAllPrimes(triadsOfInterest=('diminished'), Counts=True, Proportions=True,)
        self.assertEqual(allAugs[0], ('Overall', 80))
        self.assertEqual(allAugs[1], ('[0, 3, 6] Count', 4))
        self.assertEqual(allAugs[2], ('[0, 3, 6] Proportion', 0.05))

        afterDims = info.followChord(targetChord = '[0, 3, 6]')
        self.assertEqual(afterDims, [('[0, 3, 7]', 4)])


    def test_getIntervals(self):

        from music21 import chord

        c = chord.Chord('C4 E4 G4')
        ints = getIntervals(c)
        self.assertEqual(len(ints), 3)


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
