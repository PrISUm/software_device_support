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