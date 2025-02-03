import os
import argparse
import re
from pathlib import Path
import jsmin
import csscompressor
import htmlmin
import json
from fnmatch import fnmatch
import pathspec

class GitignoreFilter:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.spec = self._load_gitignore()

    def _load_gitignore(self):
        gitignore_path = os.path.join(self.root_dir, '.gitignore')
        if not os.path.exists(gitignore_path):
            return pathspec.PathSpec([])

        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                gitignore = f.read()
            return pathspec.PathSpec.from_lines('gitwildmatch', gitignore.splitlines())
        except Exception as e:
            print(f"Warning: Error reading .gitignore file: {str(e)}")
            return pathspec.PathSpec([])

    def is_ignored(self, path):
        # Convert absolute path to relative path from root
        rel_path = os.path.relpath(path, self.root_dir)
        return self.spec.match_file(rel_path)

def minify_content(content: str, file_type: str) -> str:
    """
    Minify content based on file type while preserving code integrity.
    """
    try:
        if file_type in ['javascript', 'typescript']:
            return jsmin.jsmin(content)
        elif file_type in ['css', 'scss']:
            return csscompressor.compress(content)
        elif file_type == 'html':
            return htmlmin.minify(content, remove_empty_space=True)
        elif file_type == 'json':
            return json.dumps(json.loads(content), separators=(',', ':'))
        elif file_type == 'svelte':
            content = re.sub(r'<!--[\s\S]*?-->', '', content)
            content = re.sub(r'<script[^>]*>([\s\S]*?)</script>', 
                           lambda m: f'<script>{jsmin.jsmin(m.group(1))}</script>', 
                           content)
            content = re.sub(r'<style[^>]*>([\s\S]*?)</style>', 
                           lambda m: f'<style>{csscompressor.compress(m.group(1))}</style>', 
                           content)
            content = re.sub(r'\s+', ' ', content)
            content = re.sub(r'>\s+<', '><', content)
            return content.strip()
        else:
            return ' '.join(content.split())
    except Exception as e:
        print(f"Warning: Minification failed for {file_type}, using original content: {str(e)}")
        return content

def should_include_file(file_path: str, exclude_patterns: list, gitignore_filter: GitignoreFilter) -> bool:
    """
    Determine if a file should be included based on exclusion patterns,
    .gitignore rules, and file types we want to skip.
    """
    # Check if file is ignored by .gitignore
    if gitignore_filter.is_ignored(file_path):
        return False
    
    # Check common skip patterns and explicitly excluded files
    skip_patterns = [
        'node_modules',
        '.git',
        '.svelte-kit',
        'build',
        '__pycache__',
        '.DS_Store',
        '.env',
        'package-lock.json',
        'package.json',
        'yarn.lock'
    ] + exclude_patterns
    
    # Check for .DS_Store files with any path
    if '.DS_Store' in file_path:
        return False
        
    # Check if the path contains node_modules anywhere
    if 'node_modules' in file_path:
        return False
    
    for pattern in skip_patterns:
        if pattern in file_path:
            return False
    
    # Skip binary files
    binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff', '.woff2', '.ttf', '.eot'}
    return Path(file_path).suffix.lower() not in binary_extensions

def get_file_type(file_path: str) -> str:
    """
    Determine the file type based on extension for proper formatting.
    """
    ext = Path(file_path).suffix.lower()
    
    file_types = {
        '.svelte': 'svelte',
        '.ts': 'typescript',
        '.js': 'javascript',
        '.css': 'css',
        '.scss': 'scss',
        '.json': 'json',
        '.md': 'markdown',
        '.html': 'html'
    }
    
    return file_types.get(ext, 'text')

def calculate_size_reduction(original: str, minified: str) -> tuple:
    """
    Calculate the size reduction achieved through minification.
    """
    original_size = len(original.encode('utf-8'))
    minified_size = len(minified.encode('utf-8'))
    reduction = ((original_size - minified_size) / original_size) * 100
    return original_size, minified_size, reduction

def format_file_content(file_path: str, content: str, file_type: str, minify: bool) -> str:
    """
    Format the file content with appropriate tags and code blocks.
    """
    relative_path = os.path.relpath(file_path)
    formatted_content = f"<file path=\"{relative_path}\" type=\"{file_type}\""
    
    if minify:
        original_content = content
        minified_content = minify_content(content, file_type)
        orig_size, min_size, reduction = calculate_size_reduction(original_content, minified_content)
        formatted_content += f" original_size=\"{orig_size}\" minified_size=\"{min_size}\" reduction=\"{reduction:.1f}%\""
        content = minified_content
    
    formatted_content += ">\n"
    formatted_content += "```" + file_type + "\n"
    formatted_content += content
    if not content.endswith('\n'):
        formatted_content += '\n'
    formatted_content += "```\n"
    formatted_content += "</file>\n\n"
    return formatted_content

def process_directory(directory: str, output_file: str, exclude_patterns: list = None, minify: bool = False) -> None:
    """
    Recursively process a directory and write formatted content to output file.
    """
    if exclude_patterns is None:
        exclude_patterns = []
    
    total_original_size = 0
    total_minified_size = 0
    gitignore_filter = GitignoreFilter(directory)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as out_file:
            out_file.write("<project>\n\n")
            
            # Write project structure
            out_file.write("<structure>\n")
            for root, dirs, files in os.walk(directory):
                # Filter out ignored directories and explicitly excluded ones
                dirs[:] = [d for d in dirs 
                          if not gitignore_filter.is_ignored(os.path.join(root, d))
                          and not any(pattern in d for pattern in exclude_patterns)
                          and d != 'node_modules'
                          and '.DS_Store' not in d]
                
                level = root.replace(directory, '').count(os.sep)
                indent = '  ' * level
                relative_path = os.path.relpath(root, directory)
                if relative_path != '.':
                    out_file.write(f"{indent}- {os.path.basename(root)}/\n")
                
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    if should_include_file(file_path, exclude_patterns, gitignore_filter):
                        out_file.write(f"{indent}  - {file}\n")
            
            out_file.write("</structure>\n\n")
            
            # Write file contents
            out_file.write("<files>\n")
            for root, _, files in os.walk(directory):
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    if should_include_file(file_path, exclude_patterns, gitignore_filter):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                file_type = get_file_type(file_path)
                                
                                if minify:
                                    orig_size = len(content.encode('utf-8'))
                                    total_original_size += orig_size
                                
                                formatted_content = format_file_content(file_path, content, file_type, minify)
                                
                                if minify:
                                    min_size = int(re.search(r'minified_size="(\d+)"', formatted_content).group(1))
                                    total_minified_size += min_size
                                
                                out_file.write(formatted_content)
                        except UnicodeDecodeError:
                            print(f"Warning: Skipping binary file {file_path}")
                        except Exception as e:
                            print(f"Error processing {file_path}: {str(e)}")
            
            out_file.write("</files>\n")
            
            if minify:
                total_reduction = ((total_original_size - total_minified_size) / total_original_size) * 100
                out_file.write(f"\n<statistics>\n")
                out_file.write(f"Total original size: {total_original_size:,} bytes\n")
                out_file.write(f"Total minified size: {total_minified_size:,} bytes\n")
                out_file.write(f"Overall reduction: {total_reduction:.1f}%\n")
                out_file.write("</statistics>\n")
            
            out_file.write("</project>")
            
    except Exception as e:
        print(f"Error writing to output file: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Generate Claude context from SvelteKit project')
    parser.add_argument('directory', help='Root directory of the SvelteKit project')
    parser.add_argument('--output', '-o', default='project_context.txt',
                      help='Output file path (default: project_context.txt)')
    parser.add_argument('--exclude', '-e', nargs='+', default=[],
                      help='Additional patterns to exclude')
    parser.add_argument('--minify', '-m', action='store_true',
                      help='Enable minification of file contents')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.directory):
        print(f"Error: {args.directory} is not a valid directory")
        return
    
    try:
        process_directory(args.directory, args.output, args.exclude, args.minify)
        print(f"Successfully generated context file at {args.output}")
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())