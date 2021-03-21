# FTP Data Loader

ftp-loader is a tool to download from and upload data files to FTP server.
It is intended to use in projects with large data files. Data files are bad 
candidates for version control managment systems. They are better to be placed
at FTP server and be downloaded on demand. 

The suggested workflow is the following. Data files are placed in folders added
to gitignore. ftp-config.toml file is used to maintain list of data files and 
their locations both at project folder and FTP. This is default name, but other
\*.toml files can be used to split file index into separate parts. Files can
be compressed.

## Installation

`pip install ftp-loader`

## Usage

`ftp-loader -h`

   Shows help.

`ftp-loader [--overwrite] [ftp-config.toml]`

   Downloads and extracts data from FTP server. Index file name is optional.
   Default index file - ftp-config.toml.


`ftp-loader --upload [--overwrite] [ftp-config.toml]`

   Compresses and uploads data to FTP server. Index file name is optional. 
   Default index file - ftp-config.toml.

`--overwrite` Option instructs to overwrite existing files.

## Index file format

Index file must contain the following parameters:


1. FTP server URL.

    `url = "server.ftp.ru"`

2. Path to project's folder at FTP. For now only Unix-style is supported.

    `path = "/projects/test-data"`

3. List of files to be transferred. It is a list of file groups. Each group
   contain 3 or 4 parameters:
   ```
   [[files]]
   dst = "work"    # Destination folder name.
   src = "storage" # Source folder name relative to 'path'.
   arch = "bz2"    # Optional. Archive type. Supported archive formats:
                   # gz, bz2
   names = [       # list of file names.
       file1.txt,
       file2.csv
   ]
   ```

   Every group of files starts with `[[files]]` header. The number of groups 
   is arbitrary.

Example of index file can be found in tests folder - ftp-config.toml.

