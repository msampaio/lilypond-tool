#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import json
import collections
import os
import subprocess
import argparse
import shutil


CONFIG_FILE = 'config.cfg'
INSTRUMENT_FILE = 'instruments.json'


class MetaData(object):
    def __init__(self):
        self.title = None

    def __repr__(self):
        return "<Meta: {}>".format(self.title)


class Score(object):
    def __init__(self):
        self.metadata = None
        self.instruments = []
        self.lily_global = None
        self.lily_layout = None
        self.lily_paper = None


    def __repr__(self):
        return "<Score: {}>".format(self.metadata.title)

    def _make_lily_front(self, instrument=None):
        if instrument:
            size = self.metadata.part_size
        else:
            size = self.metadata.score_size

        s = '\\version "{}"\n\n'.format(self.metadata.version)
        s += '\include "global.ly"\n'
        s += '\include "newcommand.ly"\n'
        if instrument:
            s += '\\include "{}.ly"\n'.format(instrument.lily_name)
        else:
            for i in self.instruments:
                s += '\\include "{}.ly"\n'.format(i.lily_name)
        s += '\n#(set-global-staff-size {})\n\n'.format(size)
        return s

    def _make_lily_score(self, instrument=None):
        s = '\score {\n'
        s += '\t<<\n'
        if instrument:
            s += '\t\set Score.skipBars = ##t'
            i = [instr for instr in self.instruments if instr == instrument][0]
            s += i.make_staff(self.metadata.sections, self.metadata.slug)
        else:
            families = self.metadata.score_groups
            for family in families:
                s += '\\new StaffGroup <<\n'
                for i in self.instruments:
                    if i.family == family:
                        s += i.make_staff(self.metadata.sections, self.metadata.slug)
                s += '>>\n'
        s += '\t>>\n'
        return s

    def _make_lily_header(self):
        s = '\header{\n'
        for k in ['title', 'composer', 'opus', 'date']:
            v = getattr(self.metadata, k)
            if v:
                s += '\t{} = "{}"\n'.format(k, v)

        if self.metadata.dedication != 'None':
            s += '\t{} = "{}"\n'.format('dedication', self.metadata.dedication)

        s += '}\n'
        return s

    def _make_lily_book(self, instrument=None):
        s = '\\book {{\n{}'.format(self._make_lily_header())
        s += '{}'.format(self._make_lily_score(instrument))
        s += '\t\midi {{ }}\n\t{}}}\n{}}}\n'.format(self.lily_layout, self.lily_paper)
        return s
        
    def make_tmp_lily_files(self):
        for i in self.instruments:
            filename = os.path.join(self.metadata.tmp_path, i.lily_name + '.ly')
            with open(filename, 'w') as f:
                f.write(i.lily_data)
        for extra in ['global', 'newcommand', 'layout', 'paper']:
            basename = extra + '.ly'
            origin_name = os.path.join(self.metadata.notes_path, basename)
            dest_name = os.path.join(self.metadata.tmp_path, basename)
            
            with open(origin_name, 'r') as f:
                lily_data = f.read()
            with open(dest_name, 'w') as f:
                f.write(lily_data)


    def make_lilypond_score(self, instrument=None):
        if not os.path.exists(self.metadata.tmp_path):
            os.mkdir(self.metadata.tmp_path)

        s = self._make_lily_front(instrument)
        s+= self._make_lily_book(instrument)
        if instrument:
            f = 'part_{}.ly'.format(instrument.lily_name)
        else:
            f = 'score.ly'
        filename = os.path.join(self.metadata.tmp_path, f)
        with open(filename, 'w') as f:
            f.write(s)
            
    def make_all_scores(self):
        self.make_lilypond_score()
        for i in self.instruments:
            self.make_lilypond_score(i)
        self.make_tmp_lily_files()
            
    def run_lilypond(self, instruments=None):
        def mount_call(filename):
            cur = os.path.abspath('.')
            outdir = os.path.join(cur, self.metadata.output_path)
            lilypath = os.path.join(cur, filename)
            tmppath = os.path.join(cur, self.metadata.tmp_path)

            s = ['{}'.format(self.metadata.lilypond_path)]
            s.append('-I')
            s.append(tmppath)
            s.append('-o')
            s.append(outdir)
            s.append(lilypath)
            return s

        if not os.path.exists(self.metadata.output_path):
            os.mkdir(self.metadata.output_path)

        if instruments:
            if type(instruments) != list:
                instruments = list(instruments)
            for i in instruments:
                basename = 'part_{}.ly'.format(i) 
                filename = os.path.join(self.metadata.tmp_path, basename)
                subprocess.call(mount_call(filename))
        else:
            filename = os.path.join(self.metadata.tmp_path, 'score.ly')
            subprocess.call(mount_call(filename))

    # FIXME: add global
    def make_notes_files(self, overwrite=False):
        for i in self.instruments:
            if os.path.exists(i.filename) and not overwrite:
                print("The file {} already exists".format(i.filename))
            else:
                s = '\\version "{}"\n\n'.format(self.metadata.version)
                s += '\\include "newcommand.ly"\n'
                for section in self.metadata.sections:
                    s += '\n{}{}{} = '.format(self.metadata.slug, section, i.lily_name)
                    s += '= \\relative c\' {\n\t\\globaldefault\n}\n'
                with open(i.filename, 'w') as f:
                    f.write(s)


class Instrument(object):
    def __init__(self):
        self.name = None
        self.abbrv = None
        self.midi = None
        self.lily_name = None

    def __repr__(self):
        return "<Instrument: {}>".format(self.name)

    def _make_sections_list(self, sections, slug):
        string = '\t\t\\' + slug
        names = ['global', self.lily_name]
        z = ['\n\t'.join([string + s + n for s in sections]) for n in names]
        return '\n'.join(['\t\t{{\n\t{}\n\t\t}}'.format(seq) for seq in z])


    def make_staff(self, sections, slug):
        s = '\t\\new Staff <<\n'
        s += '\t\t\set Staff.instrumentName = \markup {{\hcenter-in #5 \"{}\"}}\n'.format(self.name)
        s += '\t\t\set Staff.shortInstrumentName = \markup {{\hcenter-in #5 "{}"}}\n'.format(self.abbrv)
        s += '\t\t\set Staff.midiInstrument = "{}"\n'.format(self.midi)
        s += self._make_sections_list(sections, slug)
        s += '\n\t>>\n'
        return s


def get_metadata(config_file=CONFIG_FILE):
    config = configparser.ConfigParser()
    config.read(config_file, 'utf8')
    dic = {}
    for obj in config.values():
        for k, v in obj.items():
            dic.update({k: v})

    dic['sections'] = dic['sections'].split(', ')
    dic['score_groups'] = dic['score_groups'].split(', ')

    metadata = MetaData()
    metadata.__dict__ = dic

    return metadata


def get_instruments(metadata, instrument_file=INSTRUMENT_FILE):
    path = metadata.notes_path
    dic = collections.OrderedDict()
    with open(instrument_file, 'r') as f:
        dic.update(json.load(f, object_pairs_hook=collections.OrderedDict))

    instruments = []
    for family, i_list in dic.items():
        for d in i_list.values():
            obj = Instrument()
            obj.__dict__ = d
            obj.family = family
            obj.filename = os.path.join(path, obj.lily_name + '.ly')
            # FIXME
            if os.path.exists(obj.filename):
                with open(obj.filename, 'r') as f:
                    obj.lily_data = f.read()
            instruments.append(obj)

    return instruments


def get_lily_file(lily_name, metadata):
    filename = os.path.join(metadata.notes_path, lily_name + '.ly')
    with open(filename, 'r') as f:
        return f.read()


def make_score(config_file=CONFIG_FILE, instrument_file=INSTRUMENT_FILE):
    metadata = get_metadata(config_file)
    instruments = get_instruments(metadata, instrument_file)
    score = Score()
    score.metadata = metadata
    score.instruments = instruments
    score.lily_global = get_lily_file('global', metadata)
    score.lily_layout = get_lily_file('layout', metadata)
    score.lily_paper = get_lily_file('paper', metadata)
    score.lily_newcommand = get_lily_file('newcommand', metadata)
    return score


def main(config_file=CONFIG_FILE, instrument_file=INSTRUMENT_FILE):
    parser = argparse.ArgumentParser(description='Create score, parts, midi and pdf files.')
    parser.add_argument("-l", "--scores", help="Create score and parts", action='store_true')
    parser.add_argument("-s", "--pdf_score", help="Make pdf and midi files from main score", action='store_true')
    parser.add_argument("-p", "--pdf_part", help="Make pdf and midi files from given part", dest='instrument')
    parser.add_argument("-a", "--pdf_all", help="Make pdf and midi files from score and all parts", action='store_true')
    parser.add_argument("--create", help="Create notes lilypond files [y,n]", dest='overwrite')
    parser.add_argument("-c", "--clear", help="Remove output and temporary files", action='store_true')
    args = parser.parse_args()
    

    score = make_score(config_file, instrument_file)
    if any([args.scores, args.pdf_score, args.instrument, args.pdf_all]):
        score.make_all_scores()

    if args.pdf_score:
        score.run_lilypond()

    elif args.instrument:
        score.run_lilypond([args.instrument])

    elif args.pdf_all:
        instruments = map(lambda i: i.lily_name, score.instruments)
        score.run_lilypond()
        score.run_lilypond(instruments)

    elif args.clear:
        try:
            shutil.rmtree(score.metadata.output_path)
        except: print('No such file')
        try:
            shutil.rmtree(score.metadata.tmp_path)
        except: print('No such file')

    elif args.overwrite:
        if args.overwrite == 'y':
            score.make_notes_files(True)
        else:
            score.make_notes_files(False)

    

if __name__ == '__main__':
    main(CONFIG_FILE, INSTRUMENT_FILE)
