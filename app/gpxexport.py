import os
from app.exiftools import EXIF
#from lxml import etree as ET
import datetime
#import xml.dom.minidom as dom
from xml.etree import ElementTree as ET

'''
generate GPX-File from exif header
'''
def createFile(images, assets_path):
    root = ET.Element('gpx', version="1.0")
    ET.SubElement(root, 'Name').text = 'Test'

    trk = ET.SubElement(root, 'trk')
    ET.SubElement(trk, 'name').text = 'Track1'
    trkNumber = ET.SubElement(trk, 'number').text = '1'
    trkSeg = ET.SubElement(trk, 'trkseg')

    #directory = '/home/tradr/Pictures/test'
    # get filenames
    filelist = os.listdir(assets_path)
    # sort images by name
    filelist.sort()

    # create waypoints
    for filename in images:
        if filename.endswith(".JPG") or filename.endswith(".jpg"):
            #path = os.path.join(assets_path, filename)
            ex = EXIF(open(filename, 'rb'))

            geo = ex.extract_geo()
            time = ex.extract_capture_time()
            timeUTC = datetime.datetime.fromtimestamp(
            int(time)
            ).strftime('%Y-%m-%dT%H:%M:%S:%f')[:-4] + 'Z'

            trkpt = ET.SubElement(trkSeg, 'trkpt', lat=str(geo['latitude']), lon=str(geo['longitude']))
            ET.SubElement(trkpt, 'ele').text = str(geo['altitude'])
            ET.SubElement(trkpt, 'time').text = timeUTC

            continue
        else:
            continue

    # Sort trackpoints by capture date
    data = []
    for elem in trkSeg:
        key = elem.findtext("time")
        data.append((key, elem))
    
    data.sort()
    trkSeg[:] = [item[-1] for item in data]

    tree = ET.ElementTree(root)
    outfile = assets_path + '/output.gpx'
    tree.write(outfile)

