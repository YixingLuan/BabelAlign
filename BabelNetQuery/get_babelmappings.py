#!/usr/bin/env python
#-*- coding: utf-8 -*-

import codecs
from collections import defaultdict
import re
import subprocess
import os
import argparse

'''
use local BabelNet java API (in chauvin) to extract lemma-bnsyn mapping and bnsyn-translation mapping

- place this script at /local/chauvin2/yixing1/BabelNet-4.0-local/BabelNet-API-4.0.1/
- before run this script, go to /local/chauvin2/yixing1/BabelNet-4.0-local/BabelNet-API-4.0.1/ and run export CLASSPATH="..:lib/*:babelnet-api-4.0.1.jar:config"
- need to change the file path/name in ExtractBabelSynsetIDs.java and ExtractBabelTranslations.java at /local/chauvin2/yixing1/BabelNet-4.0-local/
'''

def get_target_info(idx_data):

    with codecs.open(idx_data, "r", encoding="utf-8") as tagf:
        tagged = tagf.readlines()

    # get all src focus word information
    target_info = {}
    for tag_l in tagged:
        tag_l = tag_l.rstrip("\n")
        i_id = tag_l.split("\t")[2]
        lemma = tag_l.split("\t")[3]
        pos = tag_l.split("\t")[4]
        target_info[i_id] = lemma + " " + pos
                

    return target_info


def get_lemma_bn_map(target_info, idx_data, lang, current_path):

    # work around path 
    bn_in_name = ".".join(idx_data.split("/")[-1].split(".")[:-2]) + ".in"
    bn_out_name = ".".join(idx_data.split("/")[-1].split(".")[:-2]) + ".out"

    java_in_f = codecs.open(bn_in_name, "w", encoding="utf-8")

    lemma_set = set()
    for i_id, lemma_pos in target_info.items():
        lemma = lemma_pos.split(" ")[0]
        lemma_set.add(lemma)

    for lemma in lemma_set:
        java_in_f.write(lemma)
        java_in_f.write("\n")
        
    java_in_f.close()

    # run java code to query local BabelNet (get BN synset ids for the source side focus words)
    os.chdir("BabelNet-API-4.0.1/")
    java_cmd1 = "javac -cp ..:lib/*:babelnet-api-4.0.1.jar:config ../ExtractBabelSynsetIDs.java"
    subprocess.run(java_cmd1, shell=True)
    java_cmd2 = "java -cp ..:lib/*:babelnet-api-4.0.1.jar:config ExtractBabelSynsetIDs" + " ../" + bn_in_name + " ../" + bn_out_name + " " + lang
    subprocess.run(java_cmd2, shell=True)
    os.chdir(current_path)

    with codecs.open(bn_out_name, "r", encoding="utf-8") as f:
        bnsyn_lines = f.readlines()

    bn_syn_dict = {}
    for bnsyn_line in bnsyn_lines:
        bnsyn_line = bnsyn_line.rstrip("\n").rstrip(" ")
        lemma = bnsyn_line.split("\t")[0]
        bnsyn_list = bnsyn_line.split("\t")[1].split(" ")
        bn_syn_dict[lemma] = bnsyn_list

    '''
    # save lemma-BN_syn mapping
    lemma_map = ".".join(idx_data.split(".")[:-2]) + ".lemma_bnsyn_map.txt"
    newf = codecs.open(lemma_map, "w", encoding="utf-8")
    '''

    bn_syn_set = set()
    lemma_bnsyn_map = {}
    for i_id, lemma_pos in target_info.items():
        lemma = lemma_pos.split(" ")[0]
        pos = lemma_pos.split(" ")[1]
        if lemma not in bn_syn_dict: # when lemma doesn't exist in current BabelNet == not in new gold key file
            continue
        bnsyn_list_all = bn_syn_dict[lemma]
        bnsyn_list_pos = []
        for bnsyn in bnsyn_list_all:
            if bnsyn[-1] == pos:
                bnsyn_list_pos.append(bnsyn)
                bn_syn_set.add(bnsyn)
        lemma_bnsyn_map[lemma_pos] = bnsyn_list_pos

    '''
    # write down lemma-BN_syn mapping
    for lemma_pos, bnsyn_list_pos in lemma_bnsyn_map.items():
        if bnsyn_list_pos != []:
            line = lemma_pos + "\t" + " ".join(bnsyn_list_pos) + "\n"
            newf.write(line)

    newf.close()
    '''

    rm_cmd = "rm -f " + bn_in_name
    subprocess.run(rm_cmd, shell=True)
    rm_cmd = "rm -f " + bn_out_name
    subprocess.run(rm_cmd, shell=True)

    return bn_syn_set, lemma_bnsyn_map


def get_bn_trans_map(bn_syn_set, idx_data, current_path, src_lang, lang_list):

    # work around path 
    bn_in_name = ".".join(idx_data.split("/")[-1].split(".")[:-1]) + ".in"
    bn_out_name = ".".join(idx_data.split("/")[-1].split(".")[:-1]) + ".out"

    java_in_f = codecs.open(bn_in_name, "w", encoding="utf-8")

    for bnsyn in bn_syn_set:
        line = bnsyn + "\n"
        java_in_f.write(line)

    java_in_f.close()

    # run java code to query local BabelNet (get all translations for BN synsets containing source focus word) 
    os.chdir("BabelNet-API-4.0.1/")
    java_cmd1 = "javac -cp ..:lib/*:babelnet-api-4.0.1.jar:config ../ExtractBabelTranslations.java" 
    subprocess.run(java_cmd1, shell=True)
    java_cmd2 = "java -cp ..:lib/*:babelnet-api-4.0.1.jar:config ExtractBabelTranslations" + " ../" + bn_in_name + " ../" + bn_out_name
    subprocess.run(java_cmd2, shell=True)
    os.chdir(current_path)

    f = codecs.open(bn_out_name, "r", encoding="utf-8")
    bntrans_line = f.readline()

    all_bn_lexicons = {}

    if lang_list == "":
        while bntrans_line:
            bntrans_line = bntrans_line.rstrip("\n").rstrip("\t")
            bnsyn = bntrans_line.split("\t")[0]
            trans_info_list = bntrans_line.split("\t")[1:]
            possible_bn_lex = defaultdict(set)
            for trans_info in trans_info_list:
                trans_info = trans_info.replace(" ", "_")
                source = trans_info.split(":")[0]
                lang = trans_info.split(":")[1]
                trans = trans_info.split(":")[2]
                possible_bn_lex[lang].add(trans)
            all_bn_lexicons[bnsyn] = possible_bn_lex
            bntrans_line = f.readline()
    else:
        lang_list.append(src_lang) # need to add source language as well
        while bntrans_line:
            bntrans_line = bntrans_line.rstrip("\n").rstrip("\t")
            bnsyn = bntrans_line.split("\t")[0]
            trans_info_list = bntrans_line.split("\t")[1:]
            possible_bn_lex = defaultdict(set)
            for trans_info in trans_info_list:
                trans_info = trans_info.replace(" ", "_")
                source = trans_info.split(":")[0]
                lang = trans_info.split(":")[1]
                if lang in lang_list:
                    trans = trans_info.split(":")[2]
                    possible_bn_lex[lang].add(trans)
            all_bn_lexicons[bnsyn] = possible_bn_lex
            bntrans_line = f.readline()


    f.close()

    rm_cmd = "rm -f " + bn_in_name
    subprocess.run(rm_cmd, shell=True)
    rm_cmd = "rm -f " + bn_out_name
    subprocess.run(rm_cmd, shell=True)

    return all_bn_lexicons


def clean_lemmas(lemma_list):

    symbols = re.compile("[!-/:-@[-`{-~]")
    ja_symbols = re.compile("[！？、。・「」『』【】〈〉［］≪≫《》〔〕♪ヾ†○△□×〜]")

    clean_lemma_list = set()
    for lemma in lemma_list:
        no_sym_lemma = re.sub(symbols, "", lemma) # some translations contains symbols (e.g. 発声+する)
        no_all_sym_lemma = re.sub(ja_symbols, "", no_sym_lemma)

        no_sym_lemma2 = re.sub(symbols, " ", lemma) # some translations contains symbols
        no_all_sym_lemma2 = re.sub(ja_symbols, " ", no_sym_lemma2)
        
        clean_lemma_list.add(lemma)
        clean_lemma_list.add(no_all_sym_lemma)
        clean_lemma_list.add(no_all_sym_lemma2)

    return clean_lemma_list
 

def main():

    current_path = os.getcwd()

    parser = argparse.ArgumentParser(description="query BabelNet for all translations of source focus words")

    parser.add_argument("--idx", default="", help="index list of the source focus word (e.g. output of get_tagged_idx_list.py script)") 
    parser.add_argument("--l1", default="", help="language code of the source side")
    parser.add_argument("--l2", nargs="+", default="", help="(optional) list of language codes of the target side (can specify as many lanugages as you want (space-separated))")

    args = parser.parse_args()

    idx_name = args.idx
    mapping_name = ".".join(idx_name.split(".")[:-2]) + ".bnsyn_lexicon_map.txt"

    bnsyn_trans_map = codecs.open(mapping_name, "w", encoding="utf-8")

    target_info = get_target_info(idx_name)
    bn_syn_set, lemma_bnsyn_map = get_lemma_bn_map(target_info, idx_name, args.l1, current_path)

    all_bn_lexicons = get_bn_trans_map(bn_syn_set, idx_name, current_path, args.l1, args.l2)

    for bnsyn, possible_bn_lex in all_bn_lexicons.items():
        line = bnsyn + "\t"
        for lang, lemma_list in possible_bn_lex.items():
            clean_lemma_list = clean_lemmas(lemma_list)
            line_part = lang + ":" + ",".join(clean_lemma_list)
            line += line_part + "\t"
        line = line.rstrip("\t") + "\n"
        bnsyn_trans_map.write(line)

    bnsyn_trans_map.close()
 

if __name__ == "__main__":
    main()