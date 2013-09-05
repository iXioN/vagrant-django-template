from __future__ import with_statement
from fabric.colors import green, red
from fabric.api import *
from contextlib import contextmanager as _contextmanager
from fabric.contrib import files
# globals
project_name = '{{ project_name }}'
hg_repository = 'https://rsdev.1000heads.net/%s' % (project_name, )
base_project_path = '/srv/apps'
project_path = '%s/%s' % (base_project_path, project_name, )
tasks_name = ('{{ project_name }}-beat', '{{ project_name }}-celery', )
environment_name = ""


# environments
def integration():
    "Use the integration server"
    env.hosts = ['set.your.integration.server']
    env.user = 'user'
    environment_name = "integration"

#integration shortcut
def int():
    integration()

def production():
    "Use the production server"
    env.hosts = ['set.your.prod.server']
    env.user = 'user'
    environment_name = "production"

#production shortcut
def prod():
    production()

def setup():
    """
    Setup a fresh virtualenv as well as a few useful directories, then run
    a full deployment
    """
    print(green("setup..."))
    require('hosts', provided_by=[integration, production])
    sudo('aptitude install -y python-setuptools')
    sudo('easy_install pip')
    sudo('pip install virtualenv')
    #sudo('aptitude install -y apache2')
    #sudo('aptitude install -y libapache2-mod-wsgi')
    # we want rid of the defult apache config
    #sudo('cd /etc/apache2/sites-available/; a2dissite default;')
    first_deploy()

def first_deploy():
    """
    clone and create all the requiered folder
    """
    hg_clone()
    change_rights()
    run('cd %s; virtualenv .;' % (project_path))
    deploy()

def deploy():
    """
    Deploy the latest version of the site to the servers, install any
    required third party modules, install the virtual host and 
    then restart the webserver
    """
    require('hosts', provided_by=[integration, production])
    hg_pull_update()
    install_requirements()
    #set_settings()
    #install_site()
    migrate()
    restart_webserver()
    restart_supervisor_tasks()

# Helpers. These are called by other functions rather than directly
def change_rights():
    print(green("changing the folder rights..."))
    sudo('chown -R %s:www-data %s' % (env.user, project_path))
    #sudo('chmod g+w -R %s' % (project_path))

def hg_clone():
    print(green("getting code from mercurial..."))
    with cd(base_project_path):
        run('hg clone %s %s' % (hg_repository, project_name))

def hg_pull_update():
    print(green("updating code from mercurial..."))
    #run('cd $(path)/next && rm -rf *')
    with cd(project_path):
        run('hg pull')
        run('hg update')

# def install_site():
#     "Add the virtualhost file to apache"
#     require('release', provided_by=[deploy, setup])
#     sudo('cd $(path)/releases/$(release); cp $(project_name)$(virtualhost_path)$(project_name) /etc/apache2/sites-available/')
#     sudo('cd /etc/apache2/sites-available/; a2ensite $(project_name)') 

@_contextmanager
def virtualenv():
    with cd(project_path):
        with prefix("source %s/bin/activate" % (project_path,)):
            yield

def set_settings():
    """
    dont work for now
    """
    path = "%s/{{ project_name }}/local_settings.py" % (project_path)
    if not files.exists(path):
        with virtualenv():
            run("ln -s %s_settings.py local_settings.py" % (environment_name,))

def install_requirements():
    "Install the required packages from the requirements file using pip"
    print(green("installing dependencies..."))
    with virtualenv():
        run('pip install -r requirements.txt')

def migrate():
    "Update the database"
    with virtualenv():
        run("bin/python manage.py syncdb --migrate")

def restart_webserver():
    "Restart the web server"
    print(green("reloading apache2..."))
    sudo('/etc/init.d/apache2 reload')

def restart_supervisor_tasks():
    "Restart the supervisor tasks"
    print(green("restarting supervisor tasks..."))
    for task_name in tasks_name:
        sudo('supervisorctl restart %s' % (task_name))