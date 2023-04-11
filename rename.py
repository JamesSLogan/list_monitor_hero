#!/usr/bin/env python3
#
# 
#

import os
import filecmp
import shutil

import requests
import pandas as pd

KEY =  '1AmYYhYd8iNhZG683LnOARKvCx9Anq3DeEKRmXss-Ync'
DOC = f'https://docs.google.com/spreadsheet/ccc?key={KEY}&output=csv'

SAVE_FILE = 'latest.csv'
TMP_FILE  = 'latest_tmp.csv'

def download(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.content


def fetch_doc():
    return download(DOC)


def write_tmp_file(content):
    with open(TMP_FILE, 'wb') as f:
        f.write(content)


# Overwrite saved file with tmp file
def copy_tmp():
    return shutil.copy(TMP_FILE, SAVE_FILE)


def rm_tmp():
    return os.remove(TMP_FILE)


# Returns True if newest file has no changes compared to saved one.
#
# Note that this just compares raw files but later in the code we'll be doing
# comparisons using pandas dataframes.
def no_change():
    try:
        return filecmp.cmp(SAVE_FILE, TMP_FILE)
    except FileNotFoundError:
        # Assume that SAVE_FILE is the one that's missing, this can happen on
        # the first run of this code.
        copy_tmp()
        return True


def get_df(filename):
    df = pd.read_csv(filename)

    # Strip whitespace from the whole dataframe. This shouldn't really be
    # needed but it's always possible that the document maintainer will change
    # or fix whitespace in the future, which would cause our code code to give
    # false positives.
    for column in df.columns:
        df[column] = df[column].str.strip()
    return df


def get_dfs():
    return get_df(TMP_FILE), get_df(SAVE_FILE)


# Returns all rows present in left but not in right
def get_new(left, right, cols):
    m = left.merge(right, on=cols, how='left', indicator=True)
    return m[m['_merge'] == 'left_only']


# Returns dataframe with rows added to or removed from the saved csv
def get_diffs():
    new_df, save_df = get_dfs()

    if set(new_df.columns) != set(save_df.columns):
        raise RuntimeError('csv schema changed - good luck')

    cols = list(new_df.columns)

    return get_new(new_df, save_df, cols), get_new(save_df, new_df, cols)


def main():
    # Download latest file to disk
    resp = fetch_doc()
    write_tmp_file(resp)

    # If there are no new songs we can exit now
    if no_change():
        rm_tmp()
        return

    # Get differences between files using pandas
    added, removed = get_diffs()
    return added, removed
