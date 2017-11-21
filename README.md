# CVRA Packager proposal
[![Build Status](https://travis-ci.org/cvra/packager.png)](https://travis-ci.org/cvra/packager)

This is a proposal for a simpler modules (named packages here).
It only implements the minimal amount of feature needed to get the work done :

* It can handle dependencies of modules, with diamon dependency solving. It does **not** handle circular dependency and there is currently no plan for it to do.
* It can currently generate CMakeLists for use with CppUtest, but will be extended to handle deployement on ARM and dsPIC targets using Makefiles.

## Getting started
Put the following into a file called `main.cpp` :

```cpp
#include <iostream>

int main(void)
{
    std::cout << "Hello, world!" << std::endl;
    return 0;
}
```

Now we will create the package file. Put the following into `package.yml`:

```yml
source:
    - main.cpp
```
Now to build your freshly created package run :
```sh
packager.py # Creates CMakeLists.txt
mkdir build && cd build
cmake ..
make
```

Done! You should have a `tests` executable in your current folder that will
print "Hello, World!" when launched.
You can also run `make check` to build unit tests then run them.





## Package format
The package format is based on YAML and is very minimal.
Here is a complete example showing the features of the format :

```yaml
depends:
    - example-module # Will clone from cvra/example-module
    - test-runner: # needed to generate a valid "tests" exe
        fork: antoinealb # will pull from antoinealb/test-runner instead of cvra/test-runner
    - ucos3:
        url: "https://awesomegit.com/ucos3"

source:
    - pid.c

tests:
    - tests/pid_test.cpp
```

Some explanation :

* `depends` is an array of all repository this modules relies on.
* `source` is an array of sources that should be included in both unit-test and real life application.
* `tests` is the source of all tests files.

## Running the tests

To run the tests, simply do `python -m unittest` from the root of the project.
