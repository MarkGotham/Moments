'''
===============================
SCORE SVs (scoreSVs.py)
===============================

Mark Gotham, 2019-20, for Cornell University and fourscoreandmore.org


LICENCE:
===============================

Creative Commons Attribution-NonCommercial 4.0 International License.
https://creativecommons.org/licenses/by-nc/4.0/

Please feel free to use this resource, acknowledging this source.


ABOUT:
===============================

Code for:
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

TODO:
- more tests for all options and routes

'''

from music21 import common
from music21 import pitch
from music21 import interval
from music21 import stream
from music21 import converter

from fractions import Fraction
from collections import Counter
from copy import deepcopy
from itertools import combinations
import numpy as np
import matplotlib.pyplot as plt
import csv
import os
import unittest


# ------------------------------------------------------------------------------

class TableEntry(object):
    '''
    Defines the data to be retrieved, stored, and assessed for each chord 'slice':

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
        self.extractData()


    def extractData(self):
        '''
        Extracts chord and rest info from scores.
        '''

        chordScore = self.score.chordify()
        self.data = []

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

                self.data.append(thisEntry)


    def name(self):
        '''
        Names the sv file based on any available metadata.
        '''

        self.svFileName = ''

        metadata = [x[1] for x in self.score.metadata.all()]  # Values
        if metadata == []:
            self.svFileName = 'UNNAMED_SV_FILE'
        else:
            svFileName = '_'.join(metadata)
            svFileName = svFileName.replace('.mxl', '')
            svFileName = svFileName.replace('.', '-')
            svFileName = svFileName.replace(' ', '_')
            self.svFileName = svFileName


    def makeSV(self, svFilePath=None, svFileName=None, delimiter='\t'):
        '''
        Writes the separated values file (TSV by default).
        '''

        if not svFilePath:
            svFilePath = './'

        if delimiter == '\t':
            extn = '.tsv'
        elif delimiter == ',':
            extn = '.csv'
        else:
            message = f'Delimiter (currently {delimiter}) must be either '
            message += '\'\t\' (for .tsv) or '
            message += '\',\' (for .csv).'
            raise ValueError(message)

        if svFileName:
            self.svFileName = svFileName
        else:
            self.name()

        with open(f'{svFilePath}{self.svFileName}{extn}', 'w') as svfile:
            svOut = csv.writer(svfile, delimiter=delimiter,
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

        self.inPath, self.fileName = os.path.split(svPath)

        self.parseSV()
        self.getPrimes()
        self.getNormals()

    def parseSV(self):
        '''
        Parses an SV file.
        '''

        file = f'{self.inPath}/{self.fileName}'

        f = open(file, 'r')

        self.data = []

        for row_num, line in enumerate(f):
            values = line.split('\t')
            thisEntry = TableEntry()
            thisEntry.measure = int(values[0])
            thisEntry.beat = strToFloat(values[1])
            thisEntry.beatStrength = float(values[2])  # Shouldn't need strToFloat() here
            thisEntry.length = strToFloat(values[3])
            thisEntry.pitches = values[4][2:-2].split('\', \'')
            thisEntry.intervals = values[5][2:-2].split('\', \'')
            thisEntry.primeForm = values[6]  # TODO: leave as is?
            thisEntry.normalOrder = values[7][:-1]

            self.data.append(thisEntry)

        f.close()


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


    def getPrimes(self):
        '''
        Retrieves all prime forms in a file for subsequent comparisons.
        '''

        self.primes = [entry.primeForm for entry in self.data]


    def getNormals(self):
        '''
        Retrieves all normal orders in a file for subsequent comparisons.
        '''

        self.normals = [entry.normalOrder for entry in self.data]


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

        total = len(self.primes)

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
            raise ValueError(f'Please chose one or more triad types: {optionsList}')

        if Counts:
            currentTuple = ('Overall', total)
            overallInfo.append(currentTuple)
        for triad in hitList:
            currentCount = self.primes.count(triad)
            if Counts:
                currentName = triad + ' Count'
                currentTuple = (currentName, currentCount)
                overallInfo.append(currentTuple)
            if Proportions:
                currentName = triad + ' Proportion'
                currentTuple = (currentName, currentCount/total)
                overallInfo.append(currentTuple)

        return overallInfo


    def followChord(self,
                    targetChord = '[0, 4, 8]',
                    howMany=15,
                    ignoreFirst=False):
        '''
        Get data for the chords which follow an input target chord of interest.
        '''

        # Get position info for targetChord
        positions = []
        for i in [i for i,x in enumerate(self.primes) if x == targetChord]:
            positions.append(i)

        # Retrieve following chord
        following = []
        for p in positions:
            following.append(self.primes[p + 1])

        fullCount = Counter(following)

        if ignoreFirst==True:
            start=1
        else:
            start=0

        if len(fullCount) > howMany:
            self.followCount = fullCount.most_common()[start:howMany]
        else:
            self.followCount = fullCount.most_common()[start:]

    def followCountHistogram(self, outPath=None, fileName=None):
        '''
        Get data for the chords which follow an input target chord of interest.
        Returns a histogram for whatever data has been
        assigned to self.followCount
        by self.followChord().
        '''

        labels, values = zip(*self.followCount)
        indexes = np.arange(len(labels))
        width = 0.5

        plt.bar(indexes, values, width)
        plt.title("Chord usage",fontsize=16)
        plt.xlabel("Chord type", fontsize=12)
        plt.ylabel("Count", fontsize=12)
        plt.xticks(indexes + width*0.5, labels, rotation=90)
        plt.xticks(indexes, labels, rotation=90)
        plt.gcf().subplots_adjust(bottom=0.25)

        if not outPath:
            outPath = self.inPath
        if not fileName:
            fileName = self.fileName
        plt.savefig(f'{outPath + fileName}.png', facecolor='w', edgecolor='w', format='png')

    def evenSlices(self, sliceWidth='auto'):
        '''
        Adapts the input SVs file data into a list of entries with slices of equal length.
        That length given by the shortest slice width in the data unless specified otherwise.
        Useful for certain machine learning tasks.
        '''
        # TODO: replace length with strength. Much more generalisable.
        # TODO: same process but need to associate strength with length

        self.evenSliceList = []

        sliceWidthOptions = [0.625, 0.125, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]

        if sliceWidth == 'auto':
            lengths = [entry.length for entry in self.data]
            if min(lengths) in sliceWidthOptions:
                sliceWidth = min(lengths)
            else:
                raise ValueError(f'Cannot work with the min slice width here ({sliceWidth}). '  +
                                    f'Please choose manually one from of {sliceWidthOptions}.')

        else:
            if (type(sliceWidth) not in [float, int]):
                if sliceWidth not in sliceWidthOptions:
                    raise ValueError(f'Cannot work with the slice width here {sliceWidth}. '  +
                                    f'Please choose manually one from of {sliceWidthOptions}.')

        for index in range(len(self.data)):

            entry = self.data[index]

            if entry.length > sliceWidth:
                multiplier = int(entry.length / sliceWidth)
                splitList = split(entry, multiplier)
                self.evenSliceList += splitList
            elif entry.length == sliceWidth:
                self.evenSliceList.append(entry)
            elif entry.length < sliceWidth:
                self.evenSliceList.append(entry)  # Put it in, ignore following
                count = entry.length
                while count < sliceWidth:
                    for entry in self.data[index:]:
                        count += entry.length
                        index += 1
                        # TODO: doesn't deal with syncopation

    def writeEvenMIDI(self, outPath=None, fileName=None):
        '''
        Writes a representation of the data with:
        - equal-width slices (handled by evenSlices, including the slice width);
        - one row per entry (slice);
        - whitespace-separated list of MIDI note numbers per row.
        This is designed to make it easy to read for training certain machine learning models.
        '''

        if not outPath:
            outPath = self.inPath
        if not fileName:
            fileName = self.fileName[:-4]
        fileName = fileName.replace('.', '')
        fileName = fileName.replace(' ', '_')

        text_out = open(outPath + fileName + '.txt', "w")

        for x in self.evenSliceList:
            if x.pitches != ['']:  # Shouldn't need this. Always an empty entry, even if cutting the last one out.
                ptchs = [pitch.Pitch(p) for p in x.pitches]
                text_out.write(' '.join([str(p.midi) for p in ptchs]) + '\n')

        text_out.close()


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


def split(entry, n):
    '''
    Split an entry into n shorter ones of 1/nth the length.
    '''

    shorterEntry = deepcopy(entry)
    shorterEntry.length /= n
    return [shorterEntry] * n


def strToFloat(inString):
    '''
    For processing string representations of numbers back into float.
    '''

    if '/' in inString:
        num, denom = inString.split('/')
        return round(int(num) / int(denom), 2)
    else:
        return float(inString)

# ------------------------------------------------------------------------------

class Test(unittest.TestCase):


    def test_ScoreInfoSV(self, write=False):

        from music21 import corpus

        score = corpus.parse('bach/bwv269')
        info = ScoreInfoSV(score)

        self.assertIsInstance(info, ScoreInfoSV)
        self.assertIsInstance(info.data, list)
        self.assertIsInstance(info.data[0], TableEntry)
        self.assertEqual(info.data[5].measure, 1)

        if write:
            pathToDesktop = os.path.expanduser('~') + '/Desktop/'
            info.makeSV(pathToDesktop)

    def test_SVInfo(self):

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

        info.followChord(targetChord = '[0, 3, 6]')
        self.assertEqual(info.followCount, [('[0, 3, 7]', 4)])

        # Equal slice widths
        info.evenSlices()
        for x in info.evenSliceList:
            self.assertEqual(x.length, 0.5)


    def test_getIntervals(self):

        from music21 import chord

        c = chord.Chord('C4 E4 G4')
        ints = getIntervals(c)
        self.assertEqual(len(ints), 3)


# ------------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
