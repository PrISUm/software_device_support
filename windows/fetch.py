# This must not be run directly. Run inside a docker alpine image, see generate.sh.
# It requires apk add zstd python3 7zip
import os
import re
import shutil
import subprocess
import time
import urllib.request
from tarfile import TarFile, TarInfo, LNKTYPE, SYMTYPE
from concurrent.futures import ThreadPoolExecutor

"""
This program fetches MSYS2 packages from the MSYS2 repository, extracts them,
and creates a nice directory structure and zip bundle with all the dependencies.
"""

TOOLCHAIN_VERSION = '1.0.7-pre1'
LLVM_VERSION='17.0.5'
PYTHON_VERSION='python3.11'

ENVIRONMENT = 'ucrt64'
PREFIX = 'mingw-w64-ucrt-x86_64'
MSYS2 = f'https://repo.msys2.org/mingw/{ENVIRONMENT}'

EXTRACT_ROOT = 'extract'
ROOT = os.path.join(EXTRACT_ROOT, ENVIRONMENT) 



def fetch_package_index(fetch=True):
  """
  Fetch the latest msys2 package index and return a TarFile
  to use to find package metadata
  """
  db_name = f'{ENVIRONMENT}.db'
  url = f'{MSYS2}/{db_name}'

  if fetch:
    # Download the database file (contains dependency data)
    urllib.request.urlretrieve(url, db_name)

    # Extract one layer to get the tar archive
    subprocess.check_output(f'zstd -f -d {db_name} -o {db_name}.tar', shell=True)

  # Open the tar archive for use and return it
  return TarFile(f'{db_name}.tar')

def find_package(tar: TarFile, name: str):
  """
  Find a package's full namge given the index tar and the package's short name
  """
  if name.startswith(PREFIX):
    fullname = name
  else:
    fullname = f'{PREFIX}-{name}'
  
  try:
    def is_match(fullname: str, name: str):
      # Exception for llvm/clang packages with old naming convention
      if 'llvm' in name or 'clang' in name:
        if '-14-' in name or '-15-' in name:
          return False

      return name.startswith(fullname) and not name.endswith('/desc')

      # match = re.match(r'(.*)-([0-9.]+|git-[^-]+|\d\d\d\d.)-[0-9]+$', name)
      # if match == None: return False
      # return match[1] == fullname
    
    name = next(t for t in sorted(tar.getnames()) if is_match(fullname, t))
    return (name, name[len(fullname)+1:])
  except:
    return (None, None)

def get_package_dependencies(tar: TarFile, name: str):
  """
  Return a list of dependencies needed for a package
  """
  metadata = str(tar.extractfile(f'{name}/desc').read(), 'ascii')
  # print(metadata)
  files = re.match(r'(?s).*\n%DEPENDS%\n(.*?)\n\n', metadata)
  if files == None: return []
  files = files[1].splitlines()
  files = [f.split('=')[0].split('>')[0] for f in files]

  # Exception for headers-git
  files = [f[:-4] if f.endswith('-git') and f != f'{PREFIX}-git' else f for f in files]
  return files

def get_dependencies_recursive(tar: TarFile, *names: str):
  """
  Return a list of all dependences needed for a set of packages, recursively.
  """
  to_find = list(names)
  all_names = set()
  while len(to_find):
    name = to_find.pop(0)
    (n,_) = find_package(tar, name)
    if n == None:
      print(f'Error: Could not find anything matching {name}')
      print('Possible matches:')
      for t in tar.getnames():
        if name in t:
          print(t)
      exit(1)
    all_names.add(n)
    to_find.extend(get_package_dependencies(tar, n))
  return list(all_names)

def get_download_path(name: str):
  """
  Get the downloaded tar path of a given package's full name
  """
  return os.path.realpath(os.path.join('downloads', f'{name}-any.pkg.tar'))

def fetch_package(name: str):
  """
  Download a package by its full name
  """
  path = get_download_path(name)
  url = f'{MSYS2}/{name}-any.pkg.tar.zst'
  os.makedirs('downloads', exist_ok=True)
  if os.path.isfile(path):
    print(f'* Skipping {url}')
    return path
  print(f'> Starting to download: {url}')
  urllib.request.urlretrieve(url, path + '.zst')
  print(f'< Finished downloading: {url}')
  subprocess.check_output(f'zstd -d {path}.zst -o {path}', shell=True)
  os.unlink(f'{path}.zst')
  print(f'$ Extracting:           {url}')
  return path

def fetch_packages(names: list[str]):
  """
  Download a bunch of packages by their full names
  """
  with ThreadPoolExecutor(max_workers=20) as pool:
    for name in names: pool.submit(fetch_package, name)

def extract_package(name: str, dest: str):
  """
  Extract a package by its full name into dest
  """
  path = get_download_path(name)
  print(f'> Extracting {name}')
  with TarFile(path) as tar:
    tar.extractall(dest)  
  print(f'< Finished   {name}')

def extract_packages(names: list[str], dest: str):
  """
  Extract a bunch of packages by their full names into dest
  """
  with ThreadPoolExecutor(max_workers=20) as pool:
    for name in names: pool.submit(extract_package, name, dest)

def add_github_llvm_lld(dest: str):
  """
  MSYS2 LLVM does great for compiling native on Windows, but the ld.lld.exe is not
  capable of making ELF executables for ARM. Grab the ld.lld.exe from LLVM's GitHub release
  instead.
  """
  tag = f'llvmorg-{LLVM_VERSION}'
  url = f'https://github.com/llvm/llvm-project/releases/download/{tag}/LLVM-{LLVM_VERSION}-win64.exe'
  file = os.path.basename(url)
  path = os.path.join('downloads', file)

  if not os.path.isfile(path):
    urllib.request.urlretrieve(url, path)
  
  subprocess.check_output(['7zz', 'x', path, 'bin/ld.lld.exe'])
  os.rename('bin/ld.lld.exe', os.path.join(dest, 'bin', 'ld.lld.exe'))
  os.rmdir('bin')

def compress_package(out: str, dir: str):
  """
  Compress the final package
  """
  def fix_permissions(tinfo: TarInfo):
    tinfo.uid = 0
    tinfo.gid = 0
    # Make sure every file is readable and writeable at least
    tinfo.mode |= 0o600
    if tinfo.type == LNKTYPE:
      tinfo.type = SYMTYPE
    return tinfo

  print('Compressing final archive. This will take a while.')
  with TarFile.gzopen(out, 'w') as tar:
    for s in os.scandir(dir):
      tar.add(s.path, s.name, filter=fix_permissions)

def trim_extraction(dir: str):
  # Remove share folder from the package, those aren't needed.
  # shutil.rmtree(os.path.join(dir, 'share'))
  pass

def add_version_file(dir: str):
  with open(os.path.join(dir, 'VERSION'), 'w+') as f:
    f.write(TOOLCHAIN_VERSION)

def add_certificate_bundle(tar: TarFile, dir: str):
  """
  We cannot use the main certificate store on Windows,
  so pull the Mozilla certificate trust chain from the python certifi
  package and just keep the cert.pem file in /etc/ssl/cert.pem
  """
  tarfile = fetch_package(find_package(tar, 'python-certifi')[0])
  with TarFile(tarfile) as certar:
    path = next(n for n in certar.getnames() if n.endswith('cacert.pem'))
    with open(os.path.join(dir, 'etc', 'ssl', 'cert.pem'), 'wb+') as f:
      f.write(certar.extractfile(path).read())

def add_sitecustomize_path(dir: str):
  """
  For convenience sake in python scripts, add the bin folder to path on
  every start of the python interpreter
  """
  with open(os.path.join(dir, 'lib', PYTHON_VERSION, 'site-packages', 'sitecustomize.py'), 'w+') as f:
    f.write("""\
import os
os.environ['PATH'] = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.path.pardir, os.path.pardir, os.path.pardir, 'bin')) + r'\;' + os.environ['PATH']
os.environ['PRISUM_TOOLCHAIN_PYTHON'] = 'YES'
""")

def add_activate_script(dir: str):
  """
  Create a neat little script to add the bin folder to path if needed
  """
  with open(os.path.join(dir, 'activate.bat'), 'w+') as f:
    f.write(f"""\
@echo off
set PATH=%~dp0bin\;%PATH%
""")


with fetch_package_index(True) as tar:
  deps = get_dependencies_recursive(tar, 'clang', 'lld', 'openocd', 'gdb-multiarch', 'meson', 'ninja')
  fetch_packages(deps)

  if os.path.exists(EXTRACT_ROOT): shutil.rmtree(EXTRACT_ROOT)
  time.sleep(1)
  extract_packages(deps, EXTRACT_ROOT)
  trim_extraction(ROOT)
  add_github_llvm_lld(ROOT)
  add_certificate_bundle(tar, ROOT)
  add_activate_script(ROOT)
  add_sitecustomize_path(ROOT)
  add_version_file(ROOT)
  compress_package('windows.tar.gz', ROOT)
