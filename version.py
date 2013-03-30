import subprocess

def git_version():
    proc = subprocess.Popen(['git', 'describe'], stdout=subprocess.PIPE)
    output, _ = proc.communicate()
    if proc.returncode != 0:
        raise Exception("Failed to run 'git describe'")

    version_string = output.strip()
    file('src/version.py', 'wb').write('VERSION="%s"' % version_string)
    return version_string

