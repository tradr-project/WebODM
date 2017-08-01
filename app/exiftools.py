import datetime
import exifread
import logging
import xmltodict as x2d



logger = logging.getLogger(__name__)


def eval_frac(value):
    try:
        return float(value.num) / float(value.den)
    except ZeroDivisionError:
        return None


def gps_to_decimal(values, reference):
    sign = 1 if reference in 'NE' else -1
    degrees = eval_frac(values[0])
    minutes = eval_frac(values[1])
    seconds = eval_frac(values[2])
    return sign * (degrees + minutes / 60 + seconds / 3600)


def get_float_tag(tags, key):
    if key in tags:
        return float(tags[key].values[0])
    else:
        return None


def get_frac_tag(tags, key):
    if key in tags:
        try:
            return eval_frac(tags[key].values[0])
        except ZeroDivisionError:
            return None
    else:
        return None

def extract_exif_from_file(fileobj):
    if isinstance(fileobj, (str, unicode)):
        with open(fileobj) as f:
            exif_data = EXIF(f)
    else:
        exif_data = EXIF(fileobj)
    print(exif_data)
    d = exif_data.extract_exif()
    return d


def get_xmp(fileobj):
    '''Extracts XMP metadata from and image fileobj
    '''
    img_str = str(fileobj.read())
    xmp_start = img_str.find('<x:xmpmeta')
    xmp_end = img_str.find('</x:xmpmeta')

    if xmp_start < xmp_end:
        xmp_str = img_str[xmp_start:xmp_end + 12]
        xdict = x2d.parse(xmp_str)
        xdict = xdict.get('x:xmpmeta', {})
        xdict = xdict.get('rdf:RDF', {})
        xdict = xdict.get('rdf:Description', {})
        if isinstance(xdict, list):
            return xdict
        else:
            return [xdict]
    else:
        return []


def get_gpano_from_xmp(xmp):
    for i in xmp:
        for k in i:
            if 'GPano' in k:
                return i
    return {}


class EXIF:

    def __init__(self, fileobj):
        self.tags = exifread.process_file(fileobj, details=False)
        fileobj.seek(0)
        #print(self.tags)
        #self.xmp = get_xmp(fileobj)

    def extract_image_size(self):
        # Image Width and Image Height
        if ('EXIF ExifImageWidth' in self.tags and
                'EXIF ExifImageLength' in self.tags):
            width, height = (int(self.tags['EXIF ExifImageWidth'].values[0]),
                             int(self.tags['EXIF ExifImageLength'].values[0]))
        else:
            width, height = -1, -1
        return width, height

    def extract_orientation(self):
        orientation = 1
        if 'Image Orientation' in self.tags:
            value = self.tags.get('Image Orientation').values[0]
            if type(value) == int:
                orientation = value
        return orientation

    def extract_ref_lon_lat(self):
        if 'GPS GPSLatitudeRef' in self.tags:
            reflat = self.tags['GPS GPSLatitudeRef'].values
        else:
            reflat = 'N'
        if 'GPS GPSLongitudeRef' in self.tags:
            reflon = self.tags['GPS GPSLongitudeRef'].values
        else:
            reflon = 'E'
        return reflon, reflat

    def extract_lon_lat(self):
        if 'GPS GPSLatitude' in self.tags:
            reflon, reflat = self.extract_ref_lon_lat()
            lat = gps_to_decimal(self.tags['GPS GPSLatitude'].values, reflat)
            lon = gps_to_decimal(self.tags['GPS GPSLongitude'].values, reflon)
        else:
            lon, lat = None, None
        return lon, lat

    def extract_altitude(self):
        if 'GPS GPSAltitude' in self.tags:
            altitude = eval_frac(self.tags['GPS GPSAltitude'].values[0])
        else:
            altitude = None
        return altitude

    def extract_dop(self):
        if 'GPS GPSDOP' in self.tags:
            dop = eval_frac(self.tags['GPS GPSDOP'].values[0])
        else:
            dop = None
        return dop

    def extract_geo(self):
        altitude = self.extract_altitude()
        dop = self.extract_dop()
        lon, lat = self.extract_lon_lat()
        d = {}

        if lon is not None and lat is not None:
            d['latitude'] = lat
            d['longitude'] = lon
        if altitude is not None:
            d['altitude'] = altitude
        if dop is not None:
            d['dop'] = dop
        return d

    def extract_capture_time(self):
        time_strings = [('EXIF DateTimeOriginal', 'EXIF SubSecTimeOriginal'),
                        ('EXIF DateTimeDigitized', 'EXIF SubSecTimeDigitized'),
                        ('Image DateTime', 'EXIF SubSecTime')]
        for ts in time_strings:
            if ts[0] in self.tags:
                s = str(self.tags[ts[0]].values)
                try:
                    d = datetime.datetime.strptime(s, '%Y:%m:%d %H:%M:%S')
                except ValueError:
                    continue
                timestamp = (d - datetime.datetime(1970, 1, 1)).total_seconds()   # Assuming d is in UTC
                timestamp += int(str(self.tags.get(ts[1], 0))) / 1000.0;
                return timestamp
        return 0.0

    def extract_gimbal(self):

        return dd;

    def extract_exif(self):
        width, height = self.extract_image_size()
        geo = self.extract_geo()
        capture_time = self.extract_capture_time()
        gimbal = self.extract_gimbal()
        d = {
            'orientation': orientation,
            'capture_time': capture_time,
            'gps': geo
        }
        return d
