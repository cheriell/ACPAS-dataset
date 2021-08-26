# JCP-dataset
Joint Classical Piano (JCP) dataset



Real or hand-crafted piano performances in MIDI format.

Two parts - 
Part 1: Synthesized recordings (pitch shift, multi pianos for data augmentation)
Part 2: Real recordings

each part has a training, validation, test split?

different pianos:
same as in MuseSyn-v1, test set covers one piano that do not exist in training set.

training configurations for experiments:
- model trained on both the synthesized and real recordings training sets
- test on:
    1. synthesized test set, report accuracies for trained and un-trained pianos
    2. real test set, report accuracies for trained and un-trained pianos.