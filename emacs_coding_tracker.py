#!/usr/bin/env python
# author: Bergk Pinto Benoît
# personnal project
# aim: develop a coding tracker for tracking my coding activity and saving it

# libraries
import os
import inotify.adapters
from pathlib import Path
import re
import datetime
import psutil


def read_event(filename: str, previous_file: list, bookmarks_info):
    with Path(filename).open('r') as f:
        actual_file = f.readlines()
        difference = list(set(actual_file) - set(previous_file))
        for line in difference:
            if line.startswith('''(setq command-history \'('''):
                raw_command = line.replace('''(setq command-history '((''', '')
                if raw_command.startswith(('kill-buffer', 'bookmark-jump', 'find-file')):
                    if raw_command.startswith(('kill-buffer', 'bookmark-jump')):
                        regex = '"[)].*\n'
                    else:
                        regex = '" .*\n'
                    raw_command = re.sub(
                        ' *."', '##', re.sub(regex, '', raw_command))
                    # print(raw_command)
                    # just in case I get a crazy complex command impossible to parse I take only the two first element of the split
                    command_line, target = raw_command.split('##')
                    if target.startswith('*'):
                        return ['not_file_related', ''], actual_file
                    if command_line == 'find-file':
                        return ['opening_file', re.sub('~/.*/|~/|/.*/', '', target), os.path.basename(os.path.dirname(target))], actual_file
                    elif command_line == 'bookmark-jump':
                        return ['opening_file'] + bookmarks_info[target], actual_file
                    elif command_line == 'kill-buffer':
                        return ['closing_buffer', target], actual_file
                else:
                    return ['not_file_related', ''], actual_file
        return ['not_file_related', ''], actual_file


def rm_history(filename1):
    with Path(filename1).open('w') as f2:
        f2.write('')


def get_programming_language(fileN: str):
    extension = fileN.split('.')[-1]
    if extension == 'py':
        return 'python'
    elif extension == 'sh':
        return 'bash'
    elif extension == 'pl':
        return 'perl'
    elif extension == 'org':
        return 'org-mode'
    elif extension == 'nf':
        return 'nextflow'
    else:
        return 'other-files'


def save_event_and_compute_time(event_log, events_dict, save_time_file):
    if event_log[0] == 'opening_file':
        print(f'[INFO]: starting to track file {event_log[1]}')
        events_dict[event_log[1]] = [datetime.datetime.now(), event_log[2]]
        return events_dict
    elif event_log[0] == 'closing_buffer':
        print(f'[INFO]: Recording time of coding for file {event_log[1]}')
        with Path(save_time_file).open('a') as stf:
            time_spent_on_file = datetime.datetime.now() - \
                events_dict[event_log[1]][0]
            today = datetime.datetime.today()
            programming_language = get_programming_language(event_log[1])
            with Path(save_time_file).open('a') as sft:
                sft.write(
                    f'{today}\t{time_spent_on_file}\t{programming_language}\t{event_log[1]}\t{events_dict[event_log[1]][1]}\n')
            # Don't remove as sometime we switch buffer so we don't close it totally but change the time of beginning of cound in case you donc
            del events_dict[event_log[1]]
            return events_dict


def parse_bookmaks(book_file, book_alias):
    with Path(book_file).open('r') as bf:
        previous_entry = None
        for entry in bf:
            if entry.startswith(' (filename .'):
                file_name = re.sub(' [(].*/', '', entry).replace('")\n', '')
                file_path = re.search('"(.+?)"', entry)
                alias = previous_entry.replace(
                    '(("', '').replace('("', '').replace('"\n', '')
                book_alias[alias] = [file_name,
                                     os.path.basename(os.path.dirname(file_path.group(1)))]
            else:
                previous_entry = entry
    print('[INFO]: bookmarks parsed.')
    # print(book_alias)
    return book_alias


def check_emacs_running():
    processName = 'emacs'
    for proc in psutil.process_iter():
        if processName.lower() in proc.name().lower():
            return True
    return False


def reccord_time_before_shutting_down(events_dic, save_time_file):
    for f in events_dic.keys():
        with Path(save_time_file).open('a') as stf:
            time_spent_on_file = datetime.datetime.now() - events_dic[f][0]
            today = datetime.datetime.today()
            programming_language = get_programming_language(f)
            with Path(save_time_file).open('a') as sft:
                sft.write(
                    f'{today}\t{time_spent_on_file}\t{programming_language}\t{f}\t{events_dic[f][1]}\n')


def main():
    print('[INFO]; Starting to record history of coding')
    i = inotify.adapters.Inotify()
    FILENAME = '/home/bioinfocyto/.emacs.d/history'
    FILESAVE = '/home/bioinfocyto/.emacs.d/coding_history'
    FILEBOOK = '/home/bioinfocyto/.emacs.d/bookmarks'
    # start by wiping out everything in the file
    rm_history(FILENAME)
    i.add_watch(FILENAME)
    events_saves = {}
    bookmarks = {}
    parse_bookmaks(FILEBOOK, bookmarks)
    previous_event = None
    previous_content = []
    for event in i.event_gen():
        isrunning = check_emacs_running()
        if isrunning == False:
            print('[INFO]: closing tracker as emacs is closed')
            reccord_time_before_shutting_down(events_saves, FILESAVE)
            return True
        if event is not None:
            if 'IN_CLOSE_WRITE' in event[1]:
                file_event, new_content = read_event(
                    FILENAME, previous_content, bookmarks)
                if file_event != previous_event and file_event[0] != 'not_file_related':
                    # print(file_event)
                    previous_content = new_content
                    # print(previous_content)
                    previous_event = file_event
                    events_saves = save_event_and_compute_time(
                        file_event, events_saves, FILESAVE)
                    rm_history(FILENAME)


main()
