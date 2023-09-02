# PRISUM Device Support Files
These are the CMSIS (and similar) headers for compiling board software. 

For the latest download of relevant boards, see the Releases tab.

## Administrative Use
These are downloaded from http://packs.download.atmel.com, and this repository
includes two scripts, one to fetch the URLs from the index page for relevant processors,
and another to fetch the packages themselves and create a distribution zip.

If this needs to be updated in the future, run geturls to update the list of urls in the packs file
then run package.sh. Ensure the final dist has include and svd folders for each of the relevant processors, 
then upload the device_support.zip file as a release binary.

## Packaging
Note: You need a working `zip`, `openssl`, and `7zz` (7-Zip) installation to run package.sh.

To release, just run `./package.sh`. Everything should automatically build. Docker is required to build compiler_rt libraries. Expect it to take a while.

## Note: Windows lld binary
Because Windows is such a _wonderful_ operating system, the MSYS2 Clang does not work (It will only create COFF executables, not ELF which really really breaks things).
Evidently the lld linker installed by MSYS2 above cannot create ELF files even though it can theoretically cross-compile. What that means is that it cross-compiles the code, then puts it in a COFF (Windows EXE) format so it would run on Windows if Windows were running on the compute module. Needless to say that's not going to happen anytime soon, so that clang is effectively worthless for cross compiling. We could use the LLVM below from GitHub (which was evidently built with ELF support) to cross-compile. Unfortunately, this clang requires MSVC to be installed to compile natively and that gets complicated, so we'll use the MSYS2 clang for native builds (unit tests) and steal the GitHub LLD binary (the linker) to cross-link the final binaries.

LLVM GitHub Releases: <https://github.com/llvm/llvm-project/releases>

The LLVM distribution in their GitHub Releases _does_ contain an lld which can create ELF
files, but it cannot create Windows executables. This is the bin/ld.lld binary stripped from the LLVM distribution for windows x86_64. The `-B` compiler option tells clang to search here first for the linker, so it will use this one for cross compilation.

This is the only file actually need from the LLVM distribution, so there is no longer a need to install two entire LLVM installations, this file will suffice to link compute code.

## TODO
- [ ] Add a stripped-down version of newlib for memcpy,strcpy,sprintf,etc... (Maybe custom implementation is preferred?)
- [ ] Add semihosting support?
- [ ] CI/CD this repo
