import os
import sys
import platform

import click
import boto3
import numerapi
from colorama import Fore


def exception_with_msg(msg):
    return click.ClickException(Fore.RED + msg)


def check_aws_validity(key_id, secret):
    try:
        client = boto3.client('s3',
                              aws_access_key_id=key_id,
                              aws_secret_access_key=secret)
        client.list_buckets()
        return True

    except Exception as e:
        if 'NotSignedUp' in str(e):
            raise exception_with_msg(
                '''Your AWS keys are valid, but the account is not finished signing up. You either need to update your credit card in AWS at https://portal.aws.amazon.com/billing/signup?type=resubscribe#/resubscribed, or wait up to 24 hours for their verification process to complete.'''
            )

        raise exception_with_msg(
            '''AWS keys seem to be invalid. Make sure you've entered them correctly and that your user has the necessary permissions (see https://github.com/numerai/numerai-cli/wiki/Prerequisites-Help).'''
        )


def check_numerai_validity(key_id, secret):
    try:
        napi = numerapi.NumerAPI(key_id, secret)
        napi.get_account()
        return True

    except Exception:
        raise exception_with_msg(
            '''Numerai keys seem to be invalid. Make sure you've entered them correctly.'''
        )


def is_win10_professional():
    name = sys.platform
    if name != 'win32':
        return False

    version = platform.win32_ver()[0]

    if version == '10':
        # for windows 10 only, we need to know if it's pro vs home
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion") as key:
            return winreg.QueryValueEx(key, "EditionID")[0] == 'Professional'

    return False


# error checking for docker not being installed correctly
# sadly this is a mess, since there's tons of ways to mess up your docker install, especially on windows
def root_cause(err_msg):
    if b'is not recognized as an internal or external command' in err_msg:
        if sys.platform == 'win32':
            if is_win10_professional():
                raise exception_with_msg(f"\
                    Docker does not appear to be installed. \
                    Make sure to download/install docker from https://hub.docker.com/editions/community/docker-ce-desktop-windows \n\
                    If you're sure docker is already installed, then for some reason it isn't in your PATH like expected. Restarting may fix it. \
                ")
            else:
                raise exception_with_msg(f"\
                    Docker does not appear to be installed. \
                    Make sure to download/install docker from https://github.com/docker/toolbox/releases and run \"Docker Quickstart Terminal\" when you're done. \n\
                    If you're sure docker is already installed, then for some reason it isn't in your PATH like expected. Restarting may fix it. \
                ")

    if b'command not found' in err_msg:
        if sys.platform == 'darwin':
            raise exception_with_msg(
                '''Docker does not appear to be installed. You can install it with `brew cask install docker` or from https://hub.docker.com/editions/community/docker-ce-desktop-mac'''
            )
        else:
            raise exception_with_msg(
                '''docker command not found. Please install docker and make sure that the `docker` command is in your $PATH'''
            )

    if b'This error may also indicate that the docker daemon is not running' in err_msg or b'Is the docker daemon running' in err_msg:
        if sys.platform == 'darwin':
            raise exception_with_msg(
                '''Docker daemon not running. Make sure you've started "Docker Desktop" and then run this command again.'''
            )
        elif sys.platform == 'linux2':
            raise exception_with_msg(
                '''Docker daemon not running or this user cannot acccess the docker socket. Make sure docker is running and that your user has permissions to run docker. On most systems, you can add your user to the docker group like so: `sudo groupadd docker; sudo usermod -aG docker $USER` and then restarting your computer.'''
            )
        elif sys.platform == 'win32':
            if 'DOCKER_TOOLBOX_INSTALL_PATH' in os.environ:
                raise exception_with_msg(
                    '''Docker daemon not running. Make sure you've started "Docker Quickstart Terminal" and then run this command again.'''
                )
            else:
                raise exception_with_msg(
                    '''Docker daemon not running. Make sure you've started "Docker Desktop" and then run this command again.'''
                )

    if b'invalid mode: /opt/plan' in err_msg:
        if sys.platform == 'win32':
            raise exception_with_msg(
                '''It appears that you're running Docker Toolbox, but you're not using the "Docker Quickstart Terminal". Please re-run `numerai setup` from that terminal.'''
            )

    if b'Drive has not been shared' in err_msg:
        raise exception_with_msg(
            r'''It appears that you're running from a directory that isn't shared to your docker Daemon. Make sure your directory is shared through Docker Desktop: https://docs.docker.com/docker-for-windows/#shared-drives'''
        )

    if b'No configuration files' in err_msg:
        raise exception_with_msg(
            "It appears that you're running from a directory that isn't shared to your docker Daemon. \
            Try running from a directory under your HOME, e.g. C:\\Users\\$YOUR_NAME\\$ANY_FOLDER"
        )

    print(f'Numerai CLI was unable to identify the following error:')
    print(err_msg.decode('utf8'), file=sys.stderr)