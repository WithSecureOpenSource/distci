import subprocess

def git_version():
    version_string = subprocess.check_output(['git', 'describe']).strip()
    file('src/version.py', 'wb').write('VERSION="%s"' % version_string)
    return version_string

