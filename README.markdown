# CVRA Packager proposal

This is a proposal for a simpler modules (named packages here).
It only implements the minimal amount of feature needed to get the work done :

* It can handle dependencies of modules, with diamon dependency solving. It does **not** handle circular dependency and there is currently no plan for it to do.
* It can currently generate CMakeLists for use with CppUtest, but will be extended to handle deployement on ARM and dsPIC targets using Makefiles.

## Package format
The package format is based on YAML and is very minimal.
Here is a complete example showing the features of the format :

```yaml
depends:
    - platform-abstraction
    - state-machine

source:
    - pid.c

tests:
    - tests/pid_test.cpp

test-runner: tests/main.cpp
```

Some explanation :

* `depends` is an array of all repository this modules relies on.
* `source` is an array of sources that should be included in both unit-test and real life application.
* `tests` is the source of all tests files.
* `test-runner` must contain the name of the file with the `main` function. It will only be included for the top level package.

`test-runner` feels ugly and will probably be moved in its own package.


