#!/usr/bin/env python3

"""
This script performs version-related tasks for chart directories based on Git changes.
"""

import subprocess
import sys
import os

# Check if required packages are installed and install them if necessary
try:
    import yaml
except ImportError:
    subprocess.run(['pip', 'install', 'pyyaml'], check=True)
    import yaml

def main():
    """
    Main function for performing version-related tasks on chart directories.
    """

    def increment_patch_version(version):
        """
        Increment the patch version of a given version string.
        """
        parts = version.split('.')
        if len(parts) != 3:
            raise ValueError(f'Invalid version string: {version}')
        try:
            patch = int(parts[2])
        except ValueError as exc:
            raise ValueError(f'Invalid patch version: {parts[2]}') from exc
        new_patch = patch + 1
        new_version = f'{parts[0]}.{parts[1]}.{new_patch}'
        return new_version

    # Run git command to retrieve main branch name
    git_show_remote_command = ['git', 'remote', 'show', 'origin']
    git_show_remote_command_output = subprocess.check_output(git_show_remote_command, text=True)

    # Parse output to extract main branch name
    lines = git_show_remote_command_output.split('\n')
    for line in lines:
        if line.startswith('  HEAD branch:'):
            main_branch_name = line.split(':')[1].strip()
            break

    print(main_branch_name)  # Output the main branch name

    # Get list of chart directories that have changed
    git_diff_output = subprocess.run(
        ['git', 'diff', '--name-only', 'HEAD'],
        check=True, capture_output=True, text=True
    )
    changed_files = list(git_diff_output.stdout.splitlines())

    chart_dirs = [
        os.path.dirname(file)
        for file in changed_files
        if file.endswith('/Chart.yaml') or '/templates' in file
    ]
    chart_dirs = [os.path.split(dir_path) for dir_path in chart_dirs]
    chart_dirs = [
        os.path.join(*parts[:-1]) if parts[-1] == 'templates' else os.path.join(*parts)
        for parts in chart_dirs
    ]
    chart_dirs = list(dict.fromkeys(chart_dirs))

    for chart_dir in chart_dirs:
        # Get versions
        prev_version_chart_file = subprocess.run(
            ['git', 'show', f'{main_branch_name}:{chart_dir}/Chart.yaml'],
            check=True,
            capture_output=True,
            text=True
        ).stdout
        prev_version_dict = yaml.safe_load(prev_version_chart_file)
        prev_version = prev_version_dict['version']
        with open(f'{chart_dir}/Chart.yaml', 'r', encoding='utf-8') as chart_yaml_file_content:
            current_version = [
                line.split()[1]
                for line in chart_yaml_file_content.readlines()
                if line.startswith('version:')
            ][0].strip()
        new_version = increment_patch_version(prev_version)
        # Echo previous and current versions
        print(f"The previous version is {prev_version}")
        print(f"The current version is {current_version}")

        # Check if Chart version was changed manually
        if prev_version != current_version:
            print("Chart was updated")
        else:
            print(f"Checking chart version in {chart_dir}")
            if new_version != current_version:
                print(f"Updating chart version from {current_version} to {new_version}")
                with open(f'{chart_dir}/Chart.yaml', 'r+', encoding='utf-8') as chart_yaml_file_content:
                    lines = chart_yaml_file_content.readlines()
                    chart_yaml_file_content.seek(0)
                    chart_yaml_file_content.truncate()
                    for line in lines:
                        if line.startswith('version:'):
                            chart_yaml_file_content.write(f'version: {new_version}\n')
                        else:
                            chart_yaml_file_content.write(line)
                subprocess.run(['git', 'add', f'{chart_dir}/Chart.yaml'], check=True)

if __name__ == '__main__':
    sys.exit(main())
