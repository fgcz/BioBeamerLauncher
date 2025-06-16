import textwrap


def make_dummy_biobeamer2_py(path, variant="log_files"):
    """
    Create a dummy biobeamer2.py script at the given path.
    variant: 'log_files' for log file creation, 'integration' for file copy simulation.
    """
    if variant == "log_files":
        script = textwrap.dedent(
            """
            import argparse, shutil, os, sys

            def main():
                parser = argparse.ArgumentParser()
                parser.add_argument('--xml')
                parser.add_argument('--xsd')
                parser.add_argument('--hostname')
                parser.add_argument('--log_dir')
                args = parser.parse_args()
                # Simulate work: create all expected log files in log_dir
                log_dir = args.log_dir or os.path.dirname(args.xml)
                os.makedirs(log_dir, exist_ok=True)
                with open(os.path.join(log_dir, 'biobeamer_launcher.log'), 'w') as f:
                    f.write('Launcher log\\n')
                with open(os.path.join(log_dir, 'robocopy_20250101_120000.log'), 'w') as f:
                    f.write('Robocopy log\\n')
                with open(os.path.join(log_dir, 'biobeamer_20250101_120000.log'), 'w') as f:
                    f.write('BioBeamer log\\n')
                with open(os.path.join(log_dir, f'biobeamer_subprocess_{args.hostname}.log'), 'w') as f:
                    f.write('Subprocess log\\n')
                with open(os.path.join(log_dir, 'copied_files_test_integration_scp.txt'), 'w') as f:
                    f.write('Copied files log\\n')
                sys.exit(0)

            if __name__ == '__main__':
                main()
            """
        )
    elif variant == "integration":
        script = textwrap.dedent(
            """
            import argparse, shutil, os, sys
            parser = argparse.ArgumentParser()
            parser.add_argument('--xml')
            parser.add_argument('--xsd')
            parser.add_argument('--hostname')
            parser.add_argument('--log_dir')  # Accept and use log_dir
            args = parser.parse_args()
            # Simulate work: copy a file named 'input.txt' to 'output.txt' in the same dir as xml
            src = os.path.join(os.path.dirname(args.xml), 'input.txt')
            dst = os.path.join(os.path.dirname(args.xml), 'output.txt')
            if os.path.exists(src):
                shutil.copyfile(src, dst)
                print(f'Copied {src} to {dst}')
                # Write expected log file for test
                log_dir = args.log_dir or os.path.dirname(args.xml)
                log_file = os.path.join(log_dir, f'biobeamer_{args.hostname}.log')
                os.makedirs(log_dir, exist_ok=True)
                with open(log_file, 'w') as f:
                    f.write(f'Copied {src} to {dst}\\n')
            else:
                print('No input.txt found, nothing copied')
                log_dir = args.log_dir or os.path.dirname(args.xml)
                log_file = os.path.join(log_dir, f'biobeamer_{args.hostname}.log')
                os.makedirs(log_dir, exist_ok=True)
                with open(log_file, 'w') as f:
                    f.write('No input.txt found, nothing copied\\n')
            sys.exit(0)
            """
        )
    else:
        raise ValueError("Unknown variant for make_dummy_biobeamer2_py")
    with open(path, "w") as f:
        f.write(script)


def make_dummy_pyproject_toml(path):
    toml = """[project]
name = "biobeamer2"
version = "0.0.1"
[project.scripts]
biobeamer2 = "biobeamer2:main"
"""
    with open(path, "w") as f:
        f.write(toml)
