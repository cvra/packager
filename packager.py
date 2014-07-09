#!/usr/bin/env python3
import yaml
import os.path
from subprocess import call
import jinja2


PACKAGE_REPOSITORY = "https://github.com/cvra/{package}"
BUILD_DIR = "build/"
DEPENDENCIES_DIR = "dependencies/"

def pkgfile_for_package(package):
    return os.path.join(DEPENDENCIES_DIR, package, "package.yml")

def download_dependencies(package):
    """ Download all dependencies for a given package. """

    # Skip everything if we dont have deps
    if "depends" not in package:
        return

    for dep in package["depends"]:
        repo_url = PACKAGE_REPOSITORY.format(package=dep)
        repo_path = os.path.join(DEPENDENCIES_DIR, dep)

        if not os.path.exists(repo_path):
            print("Cloning cvra/{0}...".format(dep))
            call("git clone {url} {path}".format(url=repo_url, path=repo_path).split())

        pkgfile = pkgfile_for_package(dep)
        dep = yaml.load(open(pkgfile).read())
        download_dependencies(dep)

def generate_source_list(package, category, basedir="./"):
    """
    Recursively generates a list of all source files needed to build a package
    using basedir as a path prefix.
    This function returns a set, which implies the uniqueness of file names.
    The category parameter can be "source", "tests", etc.
    """

    if category in package:
        sources = set([os.path.join(basedir, i) for i in package[category]])
    else:
        sources = set()

    if "depends" not in package:
        return sources

    for dep in package["depends"]:
        pkg_dir = os.path.join(DEPENDENCIES_DIR, dep)
        pkgfile = pkgfile_for_package(dep)
        dep = yaml.load(open(pkgfile).read())
        sources = sources.union(generate_source_list(dep, category, pkg_dir))

    return sources

def generate_source_dict(package):
    result = dict()

    for cat in ["source", "tests"]:
        result[cat] = list(generate_source_list(package, category=cat))

    result["target"] = dict()

    for arch in ["x86", "arm"]:
        result["target"][arch] = list(generate_source_list(package, category="target."+arch))

    return result

def create_jinja_env():
    template_dir = list()
    template_dir.append(os.getcwd())
    template_dir.append(os.path.dirname(__file__))
    loader = jinja2.FileSystemLoader(template_dir)
    return jinja2.Environment(loader=loader)


def render_template_to_file(template_name, dest_path, context):
    env = create_jinja_env()
    template = env.get_template(template_name)
    rendered = template.render(context)

    with open(dest_path, "w") as f:
        f.write(rendered)

def main():
    package = yaml.load(open("package.yml").read())
    download_dependencies(package)
    context = generate_source_dict(package)
    context["DEPENDENCIES_DIR"] = DEPENDENCIES_DIR

    if "templates" in package:
        for template, dest in package["templates"].items():
            render_template_to_file(template, dest, context)

    if context["tests"]:
        render_template_to_file("CMakeLists.txt.jinja", "CMakeLists.txt", context)



if __name__ == "__main__":
    main()
