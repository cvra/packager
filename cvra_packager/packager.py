#!/usr/bin/env python
import yaml
import os.path
import subprocess
import jinja2
import argparse
from collections import defaultdict
import sys

if sys.version_info.major != 3 or sys.version_info.minor < 4:
    raise RuntimeError("packager requires Python 3.4 or greater")


BUILD_DIR = "build/"
DEPENDENCIES_DIR = "dependencies"

def url_for_package(package):
    """
    Returns the correct URL for a package description.
    A simple description is just the name of the repository in the CVRA
    organization.
    Example : my_package = "pid"

    A complex repository is a dict with the only key as package name and a
    config (dict too) as value.
    Example : my_package = {"pid":{"fork":"antoinealb"}}
    """

    url_template = "https://github.com/{fork}/{package}"

    if isinstance(package, str):
        return url_template.format(fork="cvra", package=package)

    pkgname = package_name_from_desc(package)
    pkgdescr = package[pkgname]

    if "url" in pkgdescr:
        return pkgdescr["url"]

    if "fork" in pkgdescr:
        fork = pkgdescr["fork"]
        return url_template.format(fork=fork, package=pkgname)

    raise ValueError("Package must be either a string or contain a fork or URL.")

def path_for_package(package, module_map=None):
    """
    Returns the path to the downloaded package directory for given package
    description.

    It can also take a dictionnary-like object mapping a module name to its
    download folder.
    """
    package = package_name_from_desc(package)
    if module_map is None:
        package_folder = DEPENDENCIES_DIR
    else:
        package_folder = module_map[package]

    return os.path.join(package_folder, package)


def package_name_from_desc(package):
    """
    Returns the package name from a description, either simple or dictionnary.
    """
    if isinstance(package, str):
        return package

    return list(package.keys())[0]

def clone(url, dest):
    """
    Git clones the given URL to the given destination path.
    """
    command = "git clone --recursive {url} {path}".format(url=url, path=dest)
    subprocess.call(command.split())

def submodule_add(url, dest):
    """
    Adds a git submodule with the given url at the dest path.
    """
    command = "git submodule add {url} {path}".format(url=url, path=dest)
    subprocess.call(command.split())

def pkgfile_for_package(package, filemap=None):
    """
    Returns the path to the package.yml file for the given package description.
    """
    return os.path.join(path_for_package(package, filemap), "package.yml")

def open_package(package, filemap=None):
    """
    Load a package given its description / name.
    """
    pkgfile = pkgfile_for_package(package, filemap)
    return yaml.load(open(pkgfile).read())

def download_dependencies(package, method, filemap=None):
    """
    Download all dependencies for a given package.

    method is a function taking an url and a dest path and will be used for
    downloading the dependency.

    filemap is a dictionnary mapping modules name to folders.
    """
    # Skip everything if we dont have deps
    if "depends" not in package:
        return

    for dep in package["depends"]:
        repo_url = url_for_package(dep)
        repo_path = path_for_package(dep, filemap)

        if not os.path.exists(repo_path):
            method(repo_url, repo_path)

        try:
            dep = open_package(dep, filemap)
        except IOError:
            continue

        download_dependencies(dep, method=method, filemap=filemap)

def generate_source_list(package, category, filemap=None):
    """
    Recursively generates a list of all source files needed to build a package.
    The category parameter can be "source", "tests", etc.
    """

    def generate_source_set(package, category, filemap, basedir):
        if category in package:
            sources = set([os.path.join(basedir, i) for i in package[category]])
        else:
            sources = set()

        if "depends" not in package:
            return sources

        for dep in package["depends"]:
            pkg_dir = path_for_package(dep, filemap)

            # Tries to open the dependency package.yml file.
            # If it doesn't exist, simply proceed to next dependency
            try:
                dep = open_package(dep, filemap)
            except IOError:
                continue

            dep_src = generate_source_set(dep, category, filemap, pkg_dir)
            sources = sources.union(dep_src)

        return sources

    source_list = list(generate_source_set(package, category, filemap, basedir='./'))

    return sorted(source_list)

# Just needed to have a Python implementation of list because lists are not
# dynamic enough in CPython
class ListWrapper(list):
    pass

def generate_source_dict(package, filemap=None):
    """
    Generates a dictionary containing a list of files for each source category.
    The result can then be used for template rendering for example.
    """
    result = dict()

    for cat in ["source", "tests", "include_directories"]:
        result[cat] = ListWrapper(generate_source_list(package, category=cat, filemap=filemap))

    # Append test directories
    test_inc = generate_source_list(package, category="include_directories.test",
                                    filemap=filemap)
    setattr(result["include_directories"], "test", test_inc)

    result['target'] = dict()
    targets = [key for key in package.keys() if key.startswith("target.")]

    for tar in targets:
        arch = tar.replace("target.", "")
        result["target"][arch] = generate_source_list(package, category=tar, filemap=filemap)

    return result

def create_dependency_location_map(filemap):
    """
    This function receives a dependency map in the following format:
    {'control':['pid', 'odometry'], 'foo':['bar']} and converts it to the
    following format : {'pid':'control', 'odometry':'control', 'bar':'foo'}. It
    also sets a sensible default value.
    """
    locations = defaultdict(lambda: DEPENDENCIES_DIR)

    for destination, packages in filemap.items():
        for p in packages:
            locations[p] = destination

    return locations


def create_jinja_env():
    """
    Factory for a jinja2 environment with the correct paths for the packager.
    """
    template_dir = list()
    template_dir.append(os.getcwd())
    template_dir.append(os.path.dirname(__file__))
    loader = jinja2.FileSystemLoader(template_dir)
    return jinja2.Environment(loader=loader)


def render_template_to_file(template_name, dest_path, context):
    """
    Renders the template given by name to dest_path using the given context.
    """
    env = create_jinja_env()
    template = env.get_template(template_name)
    rendered = template.render(context)

    try:
        need_render = (open(dest_path, "r").read() != rendered)
    except IOError:
        need_render = True

    if need_render:
        with open(dest_path, "w") as output:
            output.write(rendered)


def parse_args(args=None):
    """
    Parses the commandline arguments.
    """
    description = "Download package dependencies and creates build files."
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--submodules', dest='download_method', action='store_const', const=submodule_add, default=clone)

    return parser.parse_args(args=args)

def main():
    """
    Main function of the application.
    """
    args = parse_args()

    try:
        package = yaml.load(open("package.yml").read())
    except FileNotFoundError:
        print('package.yml was not found. Did you forget to git add it ?')
        return

    # fixme: this redefines the constant DEPENDENCIES_DIR if dependency-dir is set for the top-level package.yml
    if 'dependency-dir' in package:
        dep = package['dependency-dir']
    else:
        dep = DEPENDENCIES_DIR

    filemap = defaultdict(lambda: dep)

    download_dependencies(package, method=args.download_method, filemap=filemap)
    context = generate_source_dict(package, filemap)

    context['include_directories'].append(dep)

    if context["tests"]:
        render_template_to_file("CMakeLists.txt.jinja", "CMakeLists.txt", context)

    if "templates" in package:
        for template, dest in package["templates"].items():
            render_template_to_file(template, dest, context)


if __name__ == "__main__":
    main()
