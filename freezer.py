#!/usr/bin/env python3

import os.path
import subprocess
import yaml

DEPENDENCIES_DIR = "dependencies/"

if __name__ == "__main__":
    versions = dict()
    original_dir = os.getcwd()
    if os.path.exists(DEPENDENCIES_DIR):
        for dir in os.listdir(DEPENDENCIES_DIR):
            dir_path = os.path.join(original_dir, DEPENDENCIES_DIR, dir)
            os.chdir(dir_path)
            git_sha = subprocess.check_output("git rev-parse HEAD".split())
            git_sha = git_sha.decode("ascii") # converts to str
            git_sha = git_sha.rstrip() # removes trailing newline
            versions[dir] = git_sha

    # default_flow_style is False to put in block mode
    print(yaml.dump(versions, default_flow_style=False))



