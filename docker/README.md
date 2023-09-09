# CICD Support Docker Containers

These docker containers are created to support CICD build times by pre-installing required components.
If a CICD job (especially the quick alpine verify build) need extra dependencies, add them to these and
push a new build.

## Ubuntu Python Versions

If you neeed to change the versions of python CICD builds against in Ubuntu, change that here and re-build the image.