#!/usr/bin/env python3

"""
This little utility can read a package.yml and run the unit tests when one of
the source or test file changes.

It is very useful when using a TDD-style of programming because you will often
find yourself doing the same steps: building and running a test after each file
change. It is also editor-independent, which is great :)
"""

from cvra_packager import generate_source_dict
import yaml
import os.path
from time import sleep
import subprocess

try:
    from termcolor import cprint
except:
    def cprint(msg, color):
        print(msg)


def run_tests(changed_path):
    """
    Run all the tests after a change in changed_path.
    """
    failure = subprocess.call("make -C build/".split(), stdout=subprocess.DEVNULL)

    if failure:
        cprint('Build failed after {} changed!'.format(changed_path), 'red')
        return

    failure = subprocess.call("build/tests".split())

    if failure:
        cprint('Tests failed after {} changed!'.format(changed_path), 'red')
        return

    cprint('All OK', 'green')

def main():
    package = yaml.load(open("package.yml").read())
    sources = generate_source_dict(package)

    if len(sources['tests']) == 0:
        print('No unit tests ? Aborting !')
        return

    files = sources['tests'] + sources['source']
    modtimes = {}

    for path in files:
        modtimes[path] = os.path.getmtime(path)

    while True:
        for path in files:
            # Vim deletes file before writing so we have to check for
            # FileNotFoundError
            try:
                mtime = os.path.getmtime(path)
            except FileNotFoundError:
                continue

            # If the file changed, run the build / tests
            if modtimes[path] != mtime:
                run_tests(path)
                modtimes[path] = mtime

        # Avoid full CPU usage
        sleep(1)

if __name__ == "__main__":
    main()
