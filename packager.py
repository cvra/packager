#!/usr/bin/env python
import yaml
import os.path
import subprocess
import jinja2


BUILD_DIR = "build/"
DEPENDENCIES_DIR = "dependencies/"

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

def path_for_package(package):
    """
    Returns the path to the downloaded package directory for given package
    description.
    """
    package = package_name_from_desc(package)
    return os.path.join(DEPENDENCIES_DIR, package)


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

def pkgfile_for_package(package):
    """
    Returns the path to the package.yml file for the given package description.
    """
    return os.path.join(path_for_package(package), "package.yml")

def open_package(package):
    """
    Load a package given its description / name.
    """
    pkgfile = pkgfile_for_package(package)
    return yaml.load(open(pkgfile).read())

def download_dependencies(package):
    """ Download all dependencies for a given package. """

    # Skip everything if we dont have deps
    if "depends" not in package:
        return

    for dep in package["depends"]:
        repo_url = url_for_package(dep)
        repo_path = path_for_package(dep)

        if not os.path.exists(repo_path):
            clone(repo_url, repo_path)

        download_dependencies(open_package(dep))

def generate_source_list(package, category):
    """
    Recursively generates a list of all source files needed to build a package.
    The category parameter can be "source", "tests", etc.
    """

    def generate_source_set(package, category, basedir):
        if category in package:
            sources = set([os.path.join(basedir, i) for i in package[category]])
        else:
            sources = set()

        if "depends" not in package:
            return sources

        for dep in package["depends"]:
            pkg_dir = path_for_package(dep)
            dep_src = generate_source_set(open_package(dep), category, pkg_dir)
            sources = sources.union(dep_src)

        return sources

    source_list = list(generate_source_set(package, category, basedir='./'))

    return sorted(source_list)

def generate_source_dict(package):
    """
    Generates a dictionary containing a list of files for each source category.
    The result can then be used for template rendering for example.
    """
    result = dict()

    for cat in ["source", "tests", "include_directories"]:
        result[cat] = generate_source_list(package, category=cat)

    result["target"] = dict()

    for arch in ["x86", "arm"]:
        result["target"][arch] = generate_source_list(package, category="target."+arch)

    return result

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

    with open(dest_path, "w") as output:
        output.write(rendered)

def main():
    """
    Main function of the application.
    """
    try:
        package = yaml.load(open("package.yml").read())
    except FileNotFoundError:
        print('package.yml was not found. Did you forget to git add it ?')
        return


    download_dependencies(package)
    context = generate_source_dict(package)
    context['include_directories'].append(DEPENDENCIES_DIR)

    if context["tests"]:
        render_template_to_file("CMakeLists.txt.jinja", "CMakeLists.txt", context)

    if "templates" in package:
        for template, dest in package["templates"].items():
            render_template_to_file(template, dest, context)


if __name__ == "__main__":
    main()
