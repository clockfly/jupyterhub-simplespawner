import os
import sys
from traitlets import Unicode
import pwd


from jupyterhub.spawner import LocalProcessSpawner


class SimpleLocalProcessSpawner(LocalProcessSpawner):
    """
    A version of LocalProcessSpawner that doesn't require users to exist on
    the system beforehand.

    Note: DO NOT USE THIS FOR PRODUCTION USE CASES! It is very insecure, and
    provides absolutely no isolation between different users!
    """

    work_directory_template = Unicode(
        '{loginuser_home}/notebooks/{username}',
        config=True,
        help="Template to expand to set the user's working directory. {userid} and {username} are expanded"
    )

    env_keep = List([
        'PATH',
        'PYTHONPATH',
        'CONDA_ROOT',
        'CONDA_DEFAULT_ENV',
        'VIRTUAL_ENV',
        'LANG',
        'LC_ALL',
        'JUPYTERLAB_DIR',
        ],
        help="""
        Whitelist of environment variables for the single-user server to inherit from the JupyterHub process.

        This whitelist is used to ensure that sensitive information in the JupyterHub process's environment
        (such as `CONFIGPROXY_AUTH_TOKEN`) is not passed to the single-user server's process.
        """
    ).tag(config=True)
    
    def loginuser(self):
        return pwd.getpwuid(os.geteuid()).pw_name

    def loginuser_home(self):
        if self.loginuser() == "root":
            return "/root"
        else:
            return "/home/" + self.loginuser()
         

    def work_directory_path(self):
      return self.work_directory_template.format(
            loginuser_home=self.loginuser_home(),
            username=self.user.name
        )

    def get_env(self):
        """Get the complete set of environment variables to be set in the spawned process."""
        env = super().get_env()
        env['PYTHONPATH'] = ":".join(sys.path)
        return env

    def make_preexec_fn(self, name):
        workdir = self.work_directory_path()
        def preexec():
            try:
                os.makedirs(workdir, 0o755, exist_ok=True)
                os.chdir(workdir)
            except e:
                print(e)
        return preexec



    def user_env(self, env):
        env['USER'] = self.user.name
        env['HOME'] = self.loginuser_home()
        env['SHELL'] = '/bin/bash'
        return env
