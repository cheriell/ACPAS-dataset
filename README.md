# Aligned Classical Piano Audio and Score (ACPAS) dataset

**ACPAS** is a dataset with aigned audio and scores for classical piano music. For each performance, we provide the corresponding **performance audio** (real recording or synthesized), **performance MIDI**, and **MIDI score**, together with **rhythm and key annotations**.

The dataset data is partly collected from a list of Automatic Music Transcription (AMT) datasets, and partly synthesized using [Native Instrument Kontakt Player](https://www.native-instruments.com/en/products/komplete/samplers/kontakt-6-player/).

List of source AMT datasets:
- MIDI Aligned Piano Sounds (MAPS) dataset
- [A-MAPS dataset](http://c4dm.eecs.qmul.ac.uk/ycart/a-maps.html)
- [Classical Piano MIDI (CPM) dataset](http://www.piano-midi.de/)
- [Aligned Scores and Performances (ASAP) dataset](https://github.com/fosfrancesco/asap-dataset)
- [MAESTRO dataset](https://magenta.tensorflow.org/datasets/maestro)

In this document, we describe a piece of music composition as a **music piece**, a version of music score to the composition as a **music score**, and a music performance to a specific music score as a **music performance**. Thus, one music piece can have multiple versions of music scores (due to e.g. different repeats), and one music score can be mapped to multiple versions of music performances.

Due to different sources of data, the performances can be human performances (from the ASAP dataset) or hand-crafted tempos and dynamics to sound like human performances (from MAPS dataset and Classical Piano MIDI Page).

## Dataset Structure

**ACPAS** dataset is composed of two subsets:
- **Real recording subset**
- **Synthetic subset**

Among all performances in the two subsets, we make sure there is no overlap between the training/validation and testing splits.

### Real recording subset

This subset covers performances with real recordings from the MAPS "ENSTDkCl" and "ENSTDkAm" subsets and the MAESTRO dataset, in total **578 performances**. The corresponding MIDI scores and annotations are from the A-MAPS dataset and the ASAP dataset.

The perforamnces from the MAPS dataset are for testing only. This is to keep inline with test data in other AMT works. The other performances from the MAESTRO dataset are divided into training, validation and testing splits.

### Synthetic subset

This subset covers performances with synthetic audios from the following three sources: 
1. Performance audio and MIDI from the MAPS synthetic subsets, and MIDI score from the A-MAPS dataset.
2. MIDI performance and score from the ASAP dataset, and audio files synthesized from performance MIDIs using [Native Instrument Kontakt Player](https://www.native-instruments.com/en/products/komplete/samplers/kontakt-6-player/).
3. MIDI performance and score from the CPM dataset, and audio files synthesized from performance MIDIs using Native Instrument Kontakt Player.

## Getting started

The data is structured as follows:

    |-- subset_R
    |   |-- composer
    |   |   |-- {piece_id}_{title}
    |   |       |-- {performance_id}_performance.wav
    |   |       |-- {performance_id}_performance.mid
    |   |       |-- {performance_id}_score.mid
    |   |-- metadata_R.csv
    |-- subset_S
        |-- composer
        |   |-- {piece_id}_{title}
        |       |-- {performance_id}_performance.wav
        |       |-- {performance_id}_performance.mid
        |       |-- {performance_id}_score.mid
        |-- metadata_S.csv
