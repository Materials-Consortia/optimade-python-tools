import re

from invoke import task

from optimade import __version__


@task
def setver(c, patch=False, new_ver=''):
    if (not patch and not new_ver) or (patch and new_ver):
        raise Exception("Either use --patch or specify e.g. --full='x.y.z.")
    if patch:
        v = [int(x) for x in __version__.split(".")]
        v[2] += 1
        new_ver = ".".join(map(str, v))
    with open("optimade/__init__.py", "r") as f:
        lines = [re.sub('__version__ = .+',
                        '__version__ = "{}"'.format(new_ver),
                        l.rstrip()) for l in f]
    with open("optimade/__init__.py", "w") as f:
        f.write("\n".join(lines))

    with open("setup.py", "r") as f:
        lines = [re.sub('version=([^,]+),',
                        'version="{}",'.format(new_ver),
                        l.rstrip()) for l in f]
    with open("setup.py", "w") as f:
        f.write("\n".join(lines))
    print("Bumped version to {}".format(new_ver))


@task
def publish(c):
    c.run("rm dist/*.*", warn=True)
    c.run("python setup.py sdist bdist_wheel")
    c.run("twine upload dist/*")