import yaml
import os.path
from subprocess import call
import jinja2


PACKAGE_REPOSITORY = "https://github.com/cvra/{package}"
BUILD_DIR = "build/"
DEPENDENCIES_DIR = "dependencies/"

def pkgfile_for_package(package):
    # pkgfile = os.path.join(repo_path, "package.yml")
    return package + ".yml"

def download_dependencies(package):
    """ Dowload all dependencies for a given package. """

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

    sources = set([os.path.join(basedir, i) for i in package[category]])

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

    result["sources"] = list(generate_source_list(package, category="source"))
    result["tests"] = list(generate_source_list(package, category="tests"))
    result["test_runner"] = package["test-runner"]

    return result


if __name__ == "__main__":
    package = yaml.load(open("pid.yml").read())
    download_dependencies(package)
    context = generate_source_dict(package)

    template = jinja2.Template(open("CMakeLists.txt.jinja").read())

    print(template.render(context))

