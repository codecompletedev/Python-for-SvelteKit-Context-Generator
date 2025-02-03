# Python for SvelteKit Context Generator

A Python script that recursively analyzes SvelteKit projects and generates a formatted text file suitable for use in Large Language Model (LLM) contexts, particularly designed for Claude.

## Features

- Recursive directory traversal of SvelteKit projects
- Intelligent file filtering based on type and content
- Built-in minification support for various file types
- Respects .gitignore patterns
- Size reduction statistics
- Support for custom exclusion patterns

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/python-for-sveltekit-context-generator.git
cd python-for-sveltekit-context-generator
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Basic usage:

```bash
python app.py /path/to/your/sveltekit/project
```

With minification enabled:

```bash
python app.py /path/to/project --minify
```

With custom output file:

```bash
python app.py /path/to/project --output custom_output.txt
```

Exclude specific patterns:

```bash
python app.py /path/to/project --exclude tests coverage
```

### Command Line Options

- `directory`: Path to the SvelteKit project (required)
- `--output`, `-o`: Output file path (default: project_context.txt)
- `--exclude`, `-e`: Additional patterns to exclude (space-separated)
- `--minify`, `-m`: Enable minification of file contents

## Output Format

The script generates a structured output file containing:

```xml
<project>
    <structure>
        <!-- Directory tree structure -->
    </structure>

    <files>
        <!-- Individual file contents with metadata -->
    </files>

    <statistics>
        <!-- Size reduction statistics (if minification enabled) -->
    </statistics>
</project>
```

## Supported File Types

- Svelte (.svelte)
- TypeScript (.ts)
- JavaScript (.js)
- CSS (.css)
- SCSS (.scss)
- JSON (.json)
- Markdown (.md)
- HTML (.html)

## Default Exclusions

The script automatically excludes:

- .DS_Store files
- node_modules directory
- package-lock.json
- package.json
- yarn.lock
- Binary files (images, fonts, etc.)
- Files matching .gitignore patterns

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
