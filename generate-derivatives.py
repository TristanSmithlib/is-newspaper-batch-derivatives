"""Generate derivatives in an Islandora newspaper batch folder
[x] HOCR tesseract OCR format
[x] OCR plain text
[ ] Aggregated ocr at issue level
[x] JP2 whatever dimensions
[x] TN 256px max
[x] JPG 767px max
[x] LARGE_JPG 1920px max
...
Sample page object: https://compass-dev.fivecolleges.edu/islandora/object/test:203/manage/datastreams

Naively searches for any instances of OBJ.xxx under the given path and places
derivatives next to them as siblings.

Searches for any file matching OBJ.*. Assumes that it's an image.
"""
import os
import runbatchprocess
import logging

TOPFOLDER = 'Y-Teen Scene-original-batched'
FILE_LIST_FILENAME = '.tmpfilelist'

# Set up basic logging
logging.basicConfig(level=logging.DEBUG)

# Use find to generate a list of OBJ files and write it to a file
# (sidestep output buffering issues with very long lists of files)
os.system("find '%s' -name 'OBJ.*' > %s" % (TOPFOLDER, FILE_LIST_FILENAME))

# Generate TN.jpg derivatives
logging.info('Generating TN.jpg derivatives')
runbatchprocess.process(FILE_LIST_FILENAME, 'convert -resize 256x256 "$objFileName" "$objDirName/TN.jpg"')
# Generate JP2.jp2 derivatives
logging.info('Generating JP2.jp2 derivatives')
#unbatchprocess.process(FILE_LIST_FILENAME, 'convert "$objFileName" "$objDirName/JP2.jp2"')
# Generate JPG.jpg derivatives (preview jpg)
logging.info('Generating JPG.jpg derivatives (preview jpg)')
#runbatchprocess.process(FILE_LIST_FILENAME, 'convert -resize 767x767 "$objFileName" "$objDirName/JPG.jpg"')
logging.info('Generating LARGE_JPG.jpg derivatives')
#runbatchprocess.process(FILE_LIST_FILENAME, 'convert -resize 1920x1920 "$objFileName" "$objDirName/LARGE_JPG.jpg"')
logging.info('Generating HOCR and OCR')
# Run tesseract, then move the output files to their proper locations
#runbatchprocess.process(FILE_LIST_FILENAME, 'tesseract "$objFileName" "$objDirName/tesseract-output" HOCR TXT && mv "$objDirName/tesseract-output.hocr" "$objDirName/HOCR" && mv "$objDirName/tesseract-output.txt" "$objDirName/OCR"')
