import os
from pathspec import PathSpec


def load_gitignore_patterns(script_dir):
    """
    Load and parse patterns from a .gitignore file in the given directory.

    Parameters:
        script_dir (str): Directory containing the .gitignore file.

    Returns:
        PathSpec or None: PathSpec object for file matching or None if not found.
    """
    gitignore_path = os.path.join(script_dir, '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as gitignore_file:
            return PathSpec.from_lines('gitwildmatch', gitignore_file)
    return None


def write_files_to_txt(output_file='output', max_file_size_mb=5):
    """
    Write file paths and contents to text files, applying exclusions and size limits.

    Parameters:
        output_file (str): Base name for output files (default: 'output').
        max_file_size_mb (int): Maximum size of each output file in MB (default: 5).
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    spec = load_gitignore_patterns(script_dir)

    current_file_index = 1
    current_file_path = f"{output_file}_{current_file_index}.txt"
    current_file_size = 0

    outfile = open(current_file_path, 'w', encoding='utf-8')

    try:
        for root, dirs, files in os.walk(script_dir):
            # Exclude hidden directories and image folders
            dirs[:] = [d for d in dirs if not d.startswith('.') and d.lower() != 'images']

            for file in files:
                # Skip hidden files, image files, and the script itself
                if file.startswith('.') or file == os.path.basename(__file__) or file.lower().endswith(
                        ('.png', '.gif')):
                    continue

                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, script_dir)

                # Skip files matching .gitignore patterns
                if spec and spec.match_file(relative_path):
                    continue

                file_header = f"{relative_path}\nfile content ...\n\n"

                # Check file size and switch to a new file if needed
                if current_file_size + len(file_header) >= max_file_size_mb * 1024 * 1024:
                    outfile.close()
                    current_file_index += 1
                    current_file_path = f"{output_file}_{current_file_index}.txt"
                    outfile = open(current_file_path, 'w', encoding='utf-8')
                    current_file_size = 0

                outfile.write(file_header)
                current_file_size += len(file_header)

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                        content = infile.read()
                        outfile.write(content)
                        current_file_size += len(content)
                except Exception as e:
                    error_message = f"Error reading file: {e}\n"
                    outfile.write(error_message)
                    current_file_size += len(error_message)

                separator = '\n' + '-' * 28 + '\n\n'
                outfile.write(separator)
                current_file_size += len(separator)
    finally:
        outfile.close()


if __name__ == '__main__':
    write_files_to_txt()
