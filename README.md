# BabAlign

This repository includes the source code for BabAlign presented in our EMNLP2020 paper [Improving Word Sense Disambiguation with Translations](https://www.aclweb.org/anthology/2020.emnlp-main.332/).

BabAlign is a precise knowledge-based word alignment algorithm using both an existing alignment tool and translations from BabelNet.
It first biases the alignment predictions of the base aligner by BabelNet translations. 
Then, it uses BabelNet translations again to fix wrong or missing alignment links. 


## Table of Contents

- [Tested Environment](#requirement)
- [Tools and Data](#tools-and-data)
- [Preprocessing](#preprocessing)
- [BabelNet Query](#babelnet-query)
- [Create Input Data](#create-input-data)
- [Run the Base Aligner](#run-the-base-aligner)
- [BabAlign](#babalign)
- [Usage Example](#usage-example)
- [References](#references)


## Tested Environment

- Python: 3.6.8
- Java: OpenJDK 1.8.0_201


## Tools and Data

- [FastAlign](https://github.com/clab/fast_align) - Used as a base aligner (any alignment tool use the same input/output format can be used as a base aligner)
- [BabelNet](https://babelnet.org/guide) - Used to query possible translations for the source focus words (We tested with java BabelNet API version 4.0.1)
- [TreeTagger](https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/) - Used for preprocessing 
- [WSD Unified Framework](http://lcl.uniroma1.it/wsdeval/) - Used as a test data (processed test datasets are available in this repository under wsd_data directory)
- [OpenSubtitles corpus](http://opus.nlpl.eu/) - Used as additional bitexts (Optional, Any bitexts can be used)


## Preprocessing

To create the input data for BabAlign, following preprocessing steps are required.

### [get_tagged_idx_list.py](https://github.com/YixingLuan/BabAlign/blob/master/preprocess/get_tagged_idx_list.py) - Save source forcus words

BabAlign takes a list of source focus words with their token ids in the source sentences to obtain aligned translations for them. 

Usage description:

```
$ python3 get_tagged_idx_list.py -h
usage: get_tagged_idx_list.py [-h]
                              [-s SOURCE] 

Get list of token ids for the tagged focus words.

arguments:
  -h, --help       show this help message and exit
  -s, --source     tsv file for lemmatized tagged source side of the text with pos ({n, v, a, r, x} notations)
```

This will create the list of source focus words with all necessary information (line number, token number, etc.) in the same directory with the input tsv file.
The input tsv file (--source) should follow the following format:

```
<lemma>    <POS tag>    <tagged_id>
```

The first column should be the source lemma, the second column is the POS tag for the lemma, and the last column should be the tagged id. 
POS tags should be described as follows:

```
nouns:      n
verbs:      v
adjectives: a
adverbs:    r
other:      x
```

Tagged id is the id used to indicate the source focus word. For the source words, which are not in focus, set `tagged_id = x`.
You can check the processed tsv files for Senseval and SemEval test sets under [wsd_data]() to see the actual format. 


### [get_lemma_pos_from_treetagger.py](https://github.com/YixingLuan/BabAlign/blob/master/preprocess/get_lemma_pos_from_treetagger.py) - Lemmatization and POS tagging

Tokenization, lemmatization and POS taggeing are required to run BabAlign.
If your data has those information, you can keep using them.
If don't, you have to run TreeTagger to obtain lemmatized and POS tagged text. 
After installing TreeTagger (directory named `TreeTagger`) under [preprocess](https://github.com/YixingLuan/BabAlign/blob/master/preprocess/), run `get_lemma_pos_from_treetagger.py` follwing the description below.

Usage description:

```
$ python3 get_lemma_pos_from_treetagger.py -h
usage: get_lemma_pos_from_treetagger.py [-h]
                                        [-i INPUT]
                                        [-l LANG] 
                                        [--lem LEM]
                                        [--pos POS]

Run and process treetagger.

arguments:
  -h, --help       show this help message and exit
  -i, --input      input data for treetagger (raw text)
  -l, --lang       language code of the input data (EN, IT, DE, ES, FR, RU)
  --lem            output filename for lemmatized text
  --pos            output filename for pos-tagged text
```

This script will produce lemmatized source text (raw text) and POS text ({n, v, a, r, x} notation) in the same directory with the input text.


## BabelNet Query

### [get_babelmappings.py](https://github.com/YixingLuan/BabAlign/blob/master/BabelNetQuery) - Querying BabelNet to obtain possible translations. 

After you download the local BabelNet java API and place the API directory (named `BabelNet-API-4.0.1`) under `BabelNetQuery` directory, you can run `get_babelmappings.py` to query possible translations. 
It will call `ExtractBabelSynsetIDs.java` and `ExtractBabelTranslations.java` to query the stored BabelNet API.

Usage description:

```
$ python3 get_babelmappings.py -h
usage: get_babelmappings.py [-h]
                            [-idx IDX]
                            [--l1 L1] 
                            [--l2 L2 [L2 ...]]

Query BabelNet for all translations of source focus words.

arguments:
  -h, --help       show this help message and exit
  --idx            index list of the source focus word (e.g. output of get_tagged_idx_list.py script)
  --l1             language code of the input data 
  --l2             (optional) list of language codes of the target side (can specify as many lanugages as you want (space-separated))
```

The input data (--idx) is the output from `get_tagged_idx_list.py`.

If `--l2` is not given, it will store all translations from all languages in BabelNet.
When the number of source focus words is large, specifying `--l2` is recommended to avoid out-of-memory issue.

This script will produce the following file:

```
*.bnsyn_lexicon_map.txt  -  list of all possible BabelNet translations (Used in combine_input.py and babelalign.py)
```

To run this script, you have to go under `BabelNetQuery` directory as follows:

```
$ cd BabelNetQuery
$ python3 get_babelmappings.py --idx source_tsv_file --l1 src_language_code (--l2 tgt_language_codes)
```

If you want to run `get_babelmappings.py` from different directory, you have to adjust paths in `line 69, 133`.


## Create Input Data

### [combine_input.py](https://github.com/YixingLuan/BabAlign/blob/master/combine_input.py) - Combine test data, additional bitexts, and BabelNet translations to create the input data.

Using the lemmatized data, BabelNet translations, and additional bitexts (optional), `combine_input.py` will create the input data for the base aligner.

Usage description:

```
$ python3 combine_input.py -h
usage: combine_input.py [-h]
                        [-s SOURCE]
                        [-t TARGET]
                        [--bi1 BI1]
                        [--bi2 BI2]
                        [-b BABELEX]
                        [--l1 L1] 
                        [--l2 L2]
                        [-o OUTPUT]

Create the input data for word aligner.

arguments:
  -h, --help       show this help message and exit
  -s, --source     lemmatized source side of the text (raw text)
  -t, --target     lemmatized target side of the text (raw text)
  --bi1            source side of the additional bitext (optional)
  --bi2            target side of the additional bitext (optional)
  --l1             language code of the source side
  --l2             language code of the target side
  -o, --output     name of the created input data for the word aligner
```

It will produce the input data (test data + additional bitext + BabelNet translations) for the base aligner.
Each line contains a source and target sentence pair separated by `" ||| "`, the separater used in the base aligner such as [FastAlign](https://github.com/clab/fast_align).
If your base aligner takes different sentence separater, please replace `" ||| "` with a proper separater. 


## Run the Base Aligner

After preparing the data, it is necessary to run the base aligner to obtain initial alignment links.
Below, we show example commands when using [FastAlign](https://github.com/clab/fast_align) (assume FastAlign package is downloaded under this directory).
Please follow the descriptions of your base aligner. 

```
$ LD_LIBRARY_PATH=/usr/local/lib64/:$LD_LIBRARY_PATH
$ export LD_LIBRARY_PATH
$ fast_align/build/fast_align -i input_name -d -o -v > output_name_forward
$ fast_align/build/fast_align -i input_name -d -o -v -r > output_name_reverse
$ fast_align/build/atools -i output_name_forward -j output_name_reverse -c intersect > output_name
```

The first 2 commands can be omitted if path to C++ compiler is properly set in your machine. 


## BabAlign

### [babelalign.py](https://github.com/YixingLuan/BabAlign/blob/master/babelalign.py) - Run BabAlign.

Finally, everything is ready for running BabAlign.

Usage description:

```
$ python3 babelalign.py -h
usage: babelalign.py [-h]
                     [-s SOURCE]
                     [-t TARGET]
                     [--idx IDX]
                     [-a ALIGNMENT]
                     [-b BABELEX]
                     [-p POS]
                     [--l1 L1] 
                     [--l2 L2]
                     [-o OUTPUT]
                     [--stop_complete]

Improve alignment accuracy by BabAlign.

arguments:
  -h, --help       show this help message and exit
  -s, --source     lemmatized source side of the text (raw text)
  -t, --target     lemmatized target side of the text (raw text)
  --idx            index list of the source focus word (e.g. output of get_tagged_idx_list.py script)
  -a, --alignment  output from word aligner
  -b, --babelex    BabelNet lexicons file (e.g. output of get_babelmappings.py script)
  -p, --pos        pos file for the target side (e.g. output of get_lemma_pos_from_treetagger.py script)
  --l1             language code of the source side
  --l2             language code of the target side
  -o, --output     name of the output file
  --stop_complete  flag to disable complete match for recovering compounds (default: False)
```

This will produce a resulting alignment file, in which each line is tab separated with the following information: 

```
<tagged_id>    <source lemma>    <aligned target lemma>    <aligned token_id pair (src-tgt format)>
```

If no alignment link is found, `<aligned target lemma>` is shown as `NONE`.

If your data has tokenization / lemmatization / POS tags provided and you don't want to change the provided tokenization, you can set the last argument `--stop_complete` to disable functionalities, which search surrounding words to recover mis-tokenized compounds. 


## Usage Example

Here, we provide a list of example commands we used when running BabAlign for Senseval-2 data.
In the following example commands, we assume we have French translation `senseval2.fr.txt` and `OpenSubtitles.en-fr` bitexts.

```
$ cd BabAlign/

# preprocess
$ python3 preprocess/get_tagged_idx_list.py -s wsd_data/senseval2.tagged.lemma.pos.tsv
$ python3 preprocess/get_lemma_pos_from_treetagger.py -i senseval2.fr.txt -l FR \
                                                      --lem senseval2.fr.lem.txt \
                                                      --pos senseval2.fr.pos.txt 
$ python3 preprocess/get_lemma_pos_from_treetagger.py -i OpenSubtitles.en-fr.en -l EN \
                                                      --lem OpenSubtitles.en-fr.en.lem.txt \
                                                      --pos OpenSubtitles.en-fr.en.pos.txt 
$ python3 preprocess/get_lemma_pos_from_treetagger.py -i OpenSubtitles.en-fr.fr -l FR \
                                                      --lem OpenSubtitles.en-fr.fr.lem.txt \
                                                      --pos OpenSubtitles.en-fr.fr.pos.txt 

# Query BabelNet
$ cd BabelNetQuery/
$ python3 get_babelmappings.py -idx wsd_data/senseval2.tagged.lemma.pos.tag_idx_list.txt --l1 EN --l2 FR DE RU
$ cd ../

# Create input data
$ python3 combine_input.py -s wsd_data/senseval2.lem.txt \
                           -t senseval2.fr.lem.txt \
                           --bi1 OpenSubtitles.en-fr.en.lem.txt \
                           --bi2 OpenSubtitles.en-fr.fr.lem.txt \
                           -b wsd_data/senseval2.tagged.lemma.pos.bnsyn_lexicon_map.txt \
                           --l1 EN \
                           --l2 FR \
                           -o senseval2.en-fr.align_in

# Run the base aligner (FastAlign in this example)
$ LD_LIBRARY_PATH=/usr/local/lib64/:$LD_LIBRARY_PATH
$ export LD_LIBRARY_PATH
$ fast_align/build/fast_align -i senseval2.en-fr.align_in -d -o -v > senseval2.en-fr.align_out
$ fast_align/build/fast_align -i senseval2.en-fr.align_in -d -o -v -r > senseval2.fr-en.align_out
$ fast_align/build/atools -i senseval2.en-fr.align_out -j senseval2.fr-en.align_out -c intersect > senseval2.en-fr.align_out_intersect

# Run BabAlign
$ python3 babelalign.py -s wsd_data/senseval2.lem.txt \
                        -t senseval2.fr.lem.txt \
                        --idx wsd_data/senseval2.tagged.lemma.pos.tag_idx_list.txt \
                        -a senseval2.en-fr.align_out_intersect \
                        -b wsd_data/senseval2.tagged.lemma.pos.bnsyn_lexicon_map.txt \
                        -p senseval2.fr.pos.txt \
                        --l1 EN \
                        --l2 FR \
                        -o senseval2.en-fr.babelalign.out
```

## References

```
@inproceedings{luan-etal-2020-improving,
    title = "Improving Word Sense Disambiguation with Translations",
    author = "Luan, Yixing  and
      Hauer, Bradley  and
      Mou, Lili  and
      Kondrak, Grzegorz",
    booktitle = "Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)",
    month = nov,
    year = "2020",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://www.aclweb.org/anthology/2020.emnlp-main.332",
    pages = "4055--4065",
}
```
