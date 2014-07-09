#!/usr/bin/env python3

import os.path
import subprocess
import json
import argparse

from contextlib import contextmanager

@contextmanager
def cd(path):
    old_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)


def dump_dict(to_dump):
    return json.dumps(to_dump, indent=2)

def load_dict(string):
    return json.loads(to_dump)

DEPENDENCIES_DIR = "dependencies/"

def load_versions_from_file(path):
    pass

def dump_versions_to_file(path):
    versions = dict()

    if not os.path.exists(DEPENDENCIES_DIR):
        return

    for dir in os.listdir(DEPENDENCIES_DIR):
        with cd(os.path.join(DEPENDENCIES_DIR, dir)):
            git_sha = subprocess.check_output("git rev-parse HEAD".split())
            git_sha = git_sha.decode("ascii") # converts to str
            git_sha = git_sha.rstrip() # removes trailing newline
            versions[dir] = git_sha

    with open(path, "w") as f:
        f.write(dump_dict(versions))


def create_argument_parser():
    """ Creates an argument parser with the correct arguments. """
    descr = "Dumps the dependencies versions into a JSON file or loads them."
    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument("-f", "--file",
            default="versions.json",
            help="Path to versions file (default: versions.json)")
    parser.add_argument("-l", "--load",
                        dest="action", action="store_const",
                        const=load_versions_from_file,
                        default=dump_versions_to_file,
                        help="Load the version from file (default: dump versions to file")

    return parser

if __name__ == "__main__":
    args = create_argument_parser().parse_args()

    args.action(args.file)




