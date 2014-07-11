#!/usr/bin/env python3

import os.path
import subprocess
import json
import argparse

from contextlib import contextmanager

from packager import DEPENDENCIES_DIR, path_for_package

@contextmanager
def cd(path):
    """
    Changes current directory to path then gets back to previous directory
    on exit.
    Similar to pushd/popd commands.
    """
    old_dir = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old_dir)


def dump_dict(to_dump):
    """ Serializes a dictionary into a string. Currently uses JSON. """
    return json.dumps(to_dump, indent=2)

def load_dict(string):
    """ Loads a dictionary from its serialized version. """
    return json.loads(string)

def load_versions_from_file(path):
    with open(path) as f:
        versions = load_dict(f.read())

    for directory, version in versions.items():
        dependency_path = path_for_package(directory)

        if os.path.exists(dependency_path):
            print("Checking out {0} at {1}".format(directory, version))
            with cd(dependency_path):
                git_cmd = "git checkout -f {0}".format(version)
                subprocess.call(git_cmd.split())


def dump_versions_to_file(path):
    versions = dict()

    if not os.path.exists(DEPENDENCIES_DIR):
        return

    for directory in os.listdir(DEPENDENCIES_DIR):
        with cd(os.path.join(DEPENDENCIES_DIR, directory)):
            git_sha = subprocess.check_output("git rev-parse HEAD".split())
            git_sha = git_sha.decode("ascii") # converts to str
            git_sha = git_sha.rstrip() # removes trailing newline
            versions[directory] = git_sha

    with open(path, "w") as output:
        output.write(dump_dict(versions))


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

def main():
    args = create_argument_parser().parse_args()
    args.action(args.file)

if __name__ == "__main__":
    main()
