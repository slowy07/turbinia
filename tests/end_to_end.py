#!/usr/bin/env python3

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import subprocess
import urllib.request
import os
import shutil
import stat
import sys
import tempfile

#TODO(aarontp): Find better non version-specific download link
# pylint: disable=line-too-long
TERRAFORM_DOWNLOAD_PATH = 'https://releases.hashicorp.com/terraform/0.12.9/terraform_0.12.9_linux_amd64.zip'
FORSETI_REPO = 'https://github.com/forseti-security/forseti-security/'
FORSETI_TERRAFORM_PATH = 'contrib/incident-response/infrastructure'


def setup(temp_dir, project):
  """Sets up Turbinia environment.

  Args:
    temp_dir (str): The directory to put temp files in.
    project (str): The GCP project name we want to deploy into.

  Returns:
    (string): The path to the Turbinia config file.
  """
  terraform_package = os.path.join(temp_dir, 'terraform.zip')
  terraform = os.path.join(temp_dir, 'terraform')
  forseti_path = os.path.join(temp_dir, 'forseti-security')
  turbinia_config = os.path.join(temp_dir, 'turbinia.conf')
  terraform_path = os.path.join(forseti_path, FORSETI_TERRAFORM_PATH)
  urllib.request.urlretrieve(TERRAFORM_DOWNLOAD_PATH, terraform_package)
  shutil.unpack_archive(terraform_package, temp_dir)
  os.chmod(terraform, stat.S_IXUSR)
  subprocess.check_call(
      'git clone {0:s} {1:s}'.format(FORSETI_REPO, forseti_path).split())
  os.chdir(terraform_path)
  cmd = 'terraform init --var="gcp_project={0:s}"'.format(project)
  subprocess.check_call(cmd.split())
  cmd = (
      'terraform apply --target=module.turbinia --var="gcp_project={0:s}" '
      '--auto-approve'.format(project))
  subprocess.check_call(cmd.split())
  cmd = 'terraform output'
  config_data = subprocess.check_output(cmd.split()).splitlines()
  # Remove first line which isn't config data
  config_data.pop(0)
  with open(turbinia_config, 'wb') as file_handle:
    file_handle.writelines(config_data)

  return turbinia_config


def main():
  """Main test function."""
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '-t', '--temp_dir', help='The name of a temporary directory for files.')
  parser.add_argument(
      '-p', '--project', required=True,
      help='The GCP project to initialize Turbinia in.')
  args = parser.parse_args()

  if args.temp_dir and not os.path.exists(args.temp_dir):
    print('Temp directory {0:s} does not exist'.format(args.temp_dir))
    sys.exit(1)
  elif args.temp_dir and os.path.exists(args.temp_dir):
    temp_dir = args.temp_dir
  else:
    temp_dir = tempfile.mkdtemp(prefix='turbinia-e2e')

  turbinia_config = setup(temp_dir, args.project)


if __name__ == '__main__':
  main()
