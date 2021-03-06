"""Generate derivatives in an Islandora newspaper batch folder
[x] HOCR tesseract OCR format
[x] OCR plain text
[x] Aggregated ocr at issue level
[x] Kakadu JP2
[x] TN 256px max
[x] JPG 767px max
[x] LARGE_JPG 1920px max
[x] FITS/TECHMD
[ ] PDF
...
Sample page object: https://compass-dev.fivecolleges.edu/islandora/object/test:203/manage/datastreams

Naively searches for any instances of OBJ.xxx under the given path and places
derivatives next to them as siblings.

Searches for any file matching OBJ.*. Assumes that it's an image.

Kakadu
------
JP2s are generated using Kakadu, which can be downloaded here:
http://kakadusoftware.com/downloads/

Make sure you configure the Kakadu path in config.py -- see README.md

"""
import os
import runbatchprocess
import logging
import argparse
from datetime import datetime
from env_setup import setupEnvironment
import math

# Execute the environment setup function from env_setup.py
setupEnvironment()

start=datetime.now()

# Use default kakadu settings from Islandora code
# EXCEPT for that num_threads is set to 1 -- long story
KAKADU_ARGUMENTS = '-num_threads 1 -rate 0.5 Clayers=1 Clevels=7 "Cprecincts={256,256},{256,256},{256,256},{128,128},{128,128},{64,64},{64,64},{32,32},{16,16}" "Corder=RPCL" "ORGgen_plt=yes" "ORGtparts=R" "Cblk={32,32}" Cuse_sop=yes'
#KAKADU_ARGUMENTS = '-num_threads 1 Creversible=yes -rate -,1,0.5,0.25'
# c.f.: https://github.com/Islandora/islandora_solution_pack_large_image/blob/7.x-release/includes/derivatives.inc#L199
# c.f.: https://groups.google.com/forum/#!topic/islandora-dev/HivVsLFSxEg

argparser = argparse.ArgumentParser()
argparser.add_argument("TOPFOLDER")
argparser.add_argument("--max-cpus", default=0, required=True, type=int, help="Number of CPUs to utilize for parallel processing")
args = argparser.parse_args()

MAX_CPUS = args.max_cpus
TOPFOLDER = args.TOPFOLDER
FILE_LIST_FILENAME = '.tmpfilelist'

# Set up basic logging
logFileName = TOPFOLDER + "derivatives-" + start.strftime('%Y%m%d-%H%M%S') + '.log'
logging.basicConfig(filename=logFileName, level=logging.DEBUG)
print("Logging to: %s" % logFileName)

#logging.getLogger("runbatchprocess").setLevel(logging.DEBUG)

logging.info('Processing folder ' + TOPFOLDER)

# Use find to generate a list of OBJ files and write it to a file
# (sidestep output buffering issues with very long lists of files)
os.system("find '%s' -name 'OBJ.*' > %s" % (TOPFOLDER, FILE_LIST_FILENAME))

logging.info('Generating TN.jpg derivatives')
runbatchprocess.process(FILE_LIST_FILENAME, 'convert -resize 256x256 "$objFileName[0]" "$objDirName/TN.jpg"', concurrentProcesses=MAX_CPUS)
logging.info('Copy representative thumbnail')
os.system("cp %s/00001/TN.jpg %s/" % (TOPFOLDER, TOPFOLDER))
logging.info('Generating JP2.jp2 derivatives')
# Kakadu doesn't like 1bit tiffs. For some reason imagemagick ignores -depth 8 when going from tif to tif so we'll use png as
# an intermediary
runbatchprocess.process(FILE_LIST_FILENAME, 'convert -compress none "$objFileName[0]" -depth 8 "$objDirName/.8bitOBJ.png"', concurrentProcesses=MAX_CPUS)
runbatchprocess.process(FILE_LIST_FILENAME, 'convert -compress none "$objDirName/.8bitOBJ.png" -depth 8 "$objDirName/.uncompressedOBJ.tif"', concurrentProcesses=MAX_CPUS)
# Then run Kakadu using the Islandora arguments
# Kakadu is multithreaded so I expected to set concurrentProcesses to 1. However I was seeing underutilization so I set Kakadu to be not multithreaded (above) and set the concurrentProcesses to a level to 39.
runbatchprocess.process(FILE_LIST_FILENAME, 'kdu_compress -i "$objDirName/.uncompressedOBJ.tif" -o "$objDirName/JP2.jp2" %s >> "$objDirName/.kakadu-`date +%%s`.log" 2>&1' % KAKADU_ARGUMENTS, concurrentProcesses=MAX_CPUS)
logging.info('Generating JPG.jpg derivatives (preview jpg)')
runbatchprocess.process(FILE_LIST_FILENAME, 'convert -resize 767x767 "$objFileName[0]" "$objDirName/JPG.jpg"', concurrentProcesses=MAX_CPUS)
logging.info('Generating LARGE_JPG.jpg derivatives')
runbatchprocess.process(FILE_LIST_FILENAME, 'convert -resize 1920x1920 "$objFileName[0]" "$objDirName/LARGE_JPG.jpg"', concurrentProcesses=MAX_CPUS)
logging.info('Generating HOCR and OCR')
# Processess file for tesseract to make them easier to read
runbatchprocess.process(FILE_LIST_FILENAME, 'convert -compress none -blur 0x2 -threshold 50% "$objDirName/.8bitOBJ.png" "$objDirName/.OCRpreprocessed.tif"', concurrentProcesses=MAX_CPUS)
# Run tesseract, then move the output files to their proper locations
runbatchprocess.process(FILE_LIST_FILENAME, 'tesseract "$objDirName/.OCRpreprocessed.tif" "$objDirName/tesseract-output" hocr txt >> "$objDirName/.tesseract-`date +%s`.log" 2>&1 && mv "$objDirName/tesseract-output.hocr" "$objDirName/HOCR.html" && mv "$objDirName/tesseract-output.txt" "$objDirName/OCR.txt" 2>&1', concurrentProcesses=MAX_CPUS/2)
# Strip out DOCTYPE tag with DTD declaration so that Islandora doesn't contact w3.org for every page on index
runbatchprocess.process(FILE_LIST_FILENAME, 'sed -i "/DOCTYPE/d" "$objDirName/HOCR.html" && sed -i "/w3\.org\/TR\/xhtml1\/DTD/d" "$objDirName/HOCR.html"', concurrentProcesses=MAX_CPUS)
# Aggregate OCR to top level object
logging.info('Aggregating OCR')
os.system("cat %s/*/OCR.txt > %s/OCR.txt" % (TOPFOLDER, TOPFOLDER))
logging.info('Generating TECHMD.xml files with Fits')
runbatchprocess.process(FILE_LIST_FILENAME, 'fits.sh -i "$objFileName" -o "$objDirName/TECHMD.xml" >>"$objDirName/.fits-`date +%s`.log" 2>&1', concurrentProcesses=MAX_CPUS/2)
# Cleanup
logging.info('Cleaning up temporary files')
runbatchprocess.process(FILE_LIST_FILENAME, 'rm "$objDirName/.8bitOBJ.png" && rm "$objDirName/.uncompressedOBJ.tif" && rm "$objDirName/.OCRpreprocessed.tif"', concurrentProcesses=1)
logging.info('Total running time: ' + str(datetime.now()-start))
