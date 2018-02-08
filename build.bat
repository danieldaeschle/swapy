echo Cleaning directories...
del -R dist
del -R swapy.egg-info
del MANIFEST
del -R .cache
echo Building packages...
python setup.py sdist
python setup.py wheel
echo Uploading to PyPi...
twine upload dist/*
echo Finished.
