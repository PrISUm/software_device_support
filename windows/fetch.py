# This must not be run directly. Run inside a docker alpine image, see generate.sh.
# It requires apk add zstd python3 7zip
import os
import re
import shutil
import subprocess
import urllib.request
from tarfile import TarFile, TarInfo
from concurrent.futures import ThreadPoolExecutor

"""
This program fetches MSYS2 packages from the MSYS2 repository, extracts them,
and creates a nice directory structure and zip bundle with all the dependencies.
"""

TOOLCHAIN_VERSION = '1.0.6-rc4'

ENVIRONMENT = 'ucrt64'
PREFIX = 'mingw-w64-ucrt-x86_64'
LLVM_VERSION='17.0.5'
MSYS2 = f'https://repo.msys2.org/mingw/{ENVIRONMENT}'

def fetch_package_index(fetch=True):
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

      match = re.match(r'(.*)-([0-9.]+|git-[^-]+|\d\d\d\d.)-[0-9]+$', name)
      if match == None: return False
      return match[1] == fullname
    
    name = next(t for t in sorted(tar.getnames()) if is_match(fullname, t))
    return (name, name[len(fullname)+1:])
  except:
    return (None, None)

def get_package_dependencies(tar: TarFile, name: str):
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
  return os.path.realpath(os.path.join('downloads', f'{name}-any.pkg.tar'))

def fetch_package(name: str):
  path = get_download_path(name)
  url = f'{MSYS2}/{name}-any.pkg.tar.zst'
  os.makedirs('downloads', exist_ok=True)
  if os.path.isfile(path):
    print(f'* Skipping {url}')
    return
  print(f'> Starting to download: {url}')
  urllib.request.urlretrieve(url, path + '.zst')
  print(f'< Finished downloading: {url}')
  subprocess.check_output(f'zstd -d {path}.zst -o {path}', shell=True)
  os.unlink(f'{path}.zst')
  print(f'$ Extracting:           {url}')

def fetch_packages(names: list[str]):
  with ThreadPoolExecutor(max_workers=20) as pool:
    for name in names: pool.submit(fetch_package, name)

def extract_package(name: str, dest: str):
  path = get_download_path(name)
  print(f'> Extracting {name}')
  with TarFile(path) as tar:
    tar.extractall(dest)  
  print(f'< Finished   {name}')

def extract_packages(names: list[str], dest: str):
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
  def fix_permissions(tinfo: TarInfo):
    tinfo.uid = 0
    tinfo.gid = 0
    # Make sure every file is readable and writeable at least
    tinfo.mode |= 0o600
    return tinfo

  print('Compressing final archive. This will take a while.')
  with TarFile.gzopen(out, 'w') as tar:
    for s in os.scandir(dir):
      tar.add(s.path, s.name, filter=fix_permissions)

def trim_extraction(dir: str):
  # Remove share, and etc folders from the package, those aren't needed.
  shutil.rmtree(os.path.join(dir, 'share'))
  shutil.rmtree(os.path.join(dir, 'etc'))

def add_version_file(dir: str):
  with open(os.path.join(dir, 'VERSION'), 'w+') as f:
    f.write(TOOLCHAIN_VERSION)

with fetch_package_index(True) as tar:
  # 'clang-tools-extra', 
  deps = get_dependencies_recursive(tar, 'clang', 'lld', 'openocd', 'gdb-multiarch', 'meson', 'ninja', 'python-certifi')
  fetch_packages(deps)
  if os.path.exists('extract'): shutil.rmtree('extract')
  extract_packages(deps, 'extract')
  trim_extraction('extract/ucrt64')
  add_github_llvm_lld('extract/ucrt64')
  add_version_file('extract/ucrt64')
  compress_package('windows.tar.gz', 'extract/ucrt64')