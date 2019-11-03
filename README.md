# Moments Musicaux

This repository provides code for identifying, storing, and retrieving musical moments according to certain specifications for use as examples in music theory and musicianship classes, for instance.
The lists and code began as supplementary material to the following paper:

Mark Gotham. 2019. Moments Musicaux: Towards Comprehensive Catalogues of Real Repertoire Examples for Teaching and Research. In 6th International Conference on Digital Libraries for Musicology (DLfM ’19), November 9, 2019, The Hague, Netherlands. ACM, New York, NY, USA, 9 pages. https://doi.org/10.1145/3358664.3358676

You are welcome to use the materials hosted here in your own work.
Please cite or otherwise acknowledge the above paper.

Pull requests for corrections and extensions are welcome.

## Code
- [scoreSVs.py](/scoreSVs.py): for creating comma or tab separated values files (.CSV, .TSV), and retrieving information such as specific chords and chord progressions.
- [moments.py](/moments.py): for segmenting melodies by rests and retrieving segments according to considerations such as interval content.

## Anthology style Listings

The paper makes reference to 8 lists hosted here:
1. [Augmented 6ths Compiled](/Anthology_Lists/Augmented_6ths/Compiled.csv),
2. [Neapolitan 6ths Compiled](/Anthology_Lists/Neapolitan/Compiled.csv),
3. [Mixed Metre, new](/Anthology_Lists/Mixed_Metre/Newly_Prepared.csv),
4. [Augmented triad: new, manual list](/Anthology_Lists/Augmented/Newly_Prepared.csv),
5. [Augmented triads in the Bach Chorales](/Anthology_Lists/Augmented/Bach_Chorales.csv),
6. [Augmented triads in Wikifonia](/Anthology_Lists/Augmented/Wikifonia.csv),
7. [Augmented triads in the Beethoven Quartets](/Anthology_Lists/Augmented/Beethoven_Quartets), and
8. 'Table' 8 refers to the hundreds of tables in the [Lieder segments folder](/LiederSegments/) which provide data (measure and offset ranges, metrical positions, and note values) for every melodic segment (separated by rests) in the vocal line of every song in the [‘Scores of Scores’ lieder corpus](https://github.com/MarkGotham/ScoresOfScores).

The set of lists itemized below expands on that initial survey and the [LiederScoreSVs folder](/LiederScoreSVs/) provides tabular 'slice' lists for every song in the [‘Scores of Scores’ lieder corpus](https://github.com/MarkGotham/ScoresOfScores) using the [scoreSVs.py](/scoreSVs.py) code, as explained in the paper.

|Corpus|Augmented Triads|Augmented Sixths|Neapolitan Sixths|L and P relations|Mixed Metre|
|---|---|---|---|---|---|
|Existing anthologies (various repertoire)|-|[X](/Anthology_Lists/Augmented_6ths/Compiled.csv)|[X](/Anthology_Lists/Neapolitan/Compiled.csv)|-|-|
|New collections (various repertoire)|[X](/Anthology_Lists/Augmented/Newly_Prepared.csv)|-|-|-|[X](/Anthology_Lists/Mixed_Metre/Newly_Prepared.csv)|
|Scores of Scores Lieder Corpus|[X](/Anthology_Lists/Augmented/Lieder_Sample.csv)|[X](/Anthology_Lists/Augmented_6ths/Lieder_Sample.csv)|[X](/Anthology_Lists/Neapolitan/)|[X](/Anthology_Lists/L_and_P/Lieder_Sample.csv)|'Le Colibri' only|
|Bach Chorales|[X](/Anthology_Lists/Augmented/Bach_Chorales.csv)|-|-|-|-|
|Beethoven String Quartets|[X](/Anthology_Lists/Augmented/Beethoven_Quartets)|-|-|-|-|
