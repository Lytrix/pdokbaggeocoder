# --------------------------------------------------------
#    __init__ - BAG geocoder init file
#
#    creation date        : 1 May 2013
#    copyright            : (c) 2013 by Eelke Jager
#    e-Mail               : info [at] lytrix.com
#
#   This plugin is based on framework of the
#   MMQGIS Geocode CSV with Google plugin created by Michael Minn.
#   Go to http://plugins.qgis.org/plugins/mmqgis/ for more information.
#
#   The geocoding is provided by the www.pdok.nl geocoding webservice:
#   Go to https://api.pdok.nl/bzk/locatieserver/search/v3_1/ui/
#   for more information.
#
#   The BAG geocoder is free software and is offered without guarantee
#   or warranty. You can redistribute it and/or modify it
#   under the terms of version 2 of the GNU General Public
#   License (GPL v2) as published by the Free Software
#   Foundation (www.gnu.org).
# --------------------------------------------------------

# utf-8

import csv
import sys
import time
import datetime
import os.path
#import urllib2
import urllib.request, urllib.parse, urllib.error
import json
import re
#from re import sub

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.core import *
from math import *
import os

# --------------------------------------------------------
#    BAG geocoder Functions
# --------------------------------------------------------


def pdokbaggeocoder_find_layer(layer_name):
    # print "find_layer(" + str(layer_name) + ")"

    for name, search_layer in QgsProject.instance().mapLayers().iteritems():
        if search_layer.name() == layer_name:
            return search_layer

    return None


def pdokbaggeocoder_is_float(s):
    try:
        float(s)
        return True
    except:
        return False


def format_float(value, separator, decimals):
    """
        Cumbersome function to give backward compatibility before python 2.7
    """
    formatstring = ("%0." + str(int(decimals)) + "f")
    # print str(value) + ": " + formatstring
    string = formatstring % value
    intend = string.find('.')
    if intend < 0:
        intend = len(string)

    if separator and (intend > 3):
        start = intend % 3
        if start == 0:
            start = 3
        intstring = string[0:start]

        for x in range(start, intend, 3):
            intstring = intstring + separator + string[x:x+3]

        string = intstring + string[intend:]

    return string


def pdokbaggeocoder_layer_attribute_bounds(layer, attribute_name):
    #attribute_index = -1
    #for index, field in layer.dataProvider().fields().iteritems():
    #   if str(field.name()) == attribute_name:
    #       attribute_index = index

    attribute_index = layer.dataProvider().fieldNameIndex(attribute_name)
    if attribute_index == -1:
        return 0, 0, 0

    # print attribute_index

    feature = QgsFeature()
    layer.dataProvider().select(layer.dataProvider().attributeIndexes())
    layer.dataProvider().rewind()

    count = 0
    minimum = 0
    maximum = 0
    while layer.dataProvider().nextFeature(feature):
        # print str(feature.attributeMap())
        # value = float(feature.attributeMap()[attribute_index])
        value, valid = feature.attributeMap()[attribute_index].toDouble()
        if (count == 0) or (minimum > value):
            minimum = value
        if (count == 0) or (maximum < value):
            maximum = value
        # print str(value) + " : " + str(valid) + " : " + str(minimum) + " : " + str(maximum)
        count += 1

    return minimum, maximum, 1


def pdokbaggeocoder_wkbtype_to_text(wkbtype):
    if wkbtype == QgsWkbTypes.Unknown: return "Unknown"
    if wkbtype == QgsWkbTypes.Point: return "point"
    if wkbtype == QgsWkbTypes.LineString: return "linestring"
    if wkbtype == QgsWkbTypes.Polygon: return "polygon"
    if wkbtype == QgsWkbTypes.MultiPoint: return "multipoint"
    if wkbtype == QgsWkbTypes.MultiLineString: return "multilinestring"
    if wkbtype == QgsWkbTypes.MultiPolygon: return "multipolygon"
    # if wkbtype == QgsWkbTypes.NoGeometry: return "no geometry"
    if wkbtype == QgsWkbTypes.Point25D: return "point 2.5d"
    if wkbtype == QgsWkbTypes.LineString25D: return "linestring 2.5D"
    if wkbtype == QgsWkbTypes.Polygon25D: return "multipolygon 2.5D"
    if wkbtype == QgsWkbTypes.MultiPoint25D: return "multipoint 2.5D"
    if wkbtype == QgsWkbTypes.MultiLineString25D: return "multilinestring 2.5D"
    if wkbtype == QgsWkbTypes.MultiPolygon25D: return "multipolygon 2.5D"
    return "Unknown WKB " + str(wkbtype)


def pdokbaggeocoder_status_message(qgis, message):
    qgis.mainWindow().statusBar().showMessage(message)


# --------------------------------------------------------------
#    BAG_geocode_pdok - Geocode CSV points from Pdok
# --------------------------------------------------------------


def pdokbaggeocoder(qgis, csvname, shapefilename, notfoundfile, keys, addlayer, current_city, start_time):
    if (not csvname) or (len(csvname) <= 0):
        return "No CSV address file given"
    # Read the CSV file header
    try:
        infile = open(csvname, 'r')
    except EnvironmentError:
        return "Fout bij het openen van " + csvname

    try:
        dialect = csv.Sniffer().sniff(infile.readline(), [',', ';', ';', '|'],)
    except:
        return "Fout bij het openen van " + str(csvname) + ": " + str(sys.exc_info()[1]) + "Controleer of de scheidingstekens consistent zijn gekozen en deze niet in de velden voorkomen."

    fields = QgsFields()
    indices = []

    if current_city != "":
        selected_city = "+" + urllib.parse.quote(current_city)
    else:
        selected_city = ""

    try:
        infile.seek(0)
        reader = csv.reader(infile, dialect)
        header = reader.__next__()
    except:
        return "Fout bij het lezen van " + str(csvname) + ": " + str(sys.exc_info()[1])

    for x in range(0, len(header)):
        for y in range(0, len(keys)):
            if header[x] == keys[y]:
                indices.append(x)

        fieldname = header[x].strip()
        fields.append(QgsField(fieldname[0:9], QVariant.String))

    if (len(fields) <= 0) or (len(indices) <= 0):
        return "Geen geldige adresvelden in " + csvname

    # Create the CSV file for ungeocoded records
    try:
        notfound = open(notfoundfile, 'w')
    except:
        return "Kan het bestand %s niet openen." % notfoundfile

    notwriter = csv.writer(notfound, dialect=csv.excel)
    notwriter.writerow(header)

    # Create the output shapefile
    if QFile(shapefilename).exists():
        if not QgsVectorFileWriter.deleteShapeFile(shapefilename):
            return "Kan shapefile: " + str(shapefilename) + "niet openen."

    crs = QgsCoordinateReferenceSystem()
    crs.createFromSrid(28992)
    outfile = QgsVectorFileWriter(shapefilename, "System", fields, QgsWkbTypes.Point, crs, 'ESRI Shapefile')

    if (outfile.hasError() != QgsVectorFileWriter.NoError):
        return "Schrijffout bij het aanmaken van de shapefile: " + str(outfile.errorMessage())

    # Geocode and import
    recordcount = 0
    notfoundcount = 0
    url_list = []
    notfound_list = []
    for row in reader:
        recordcount += 1
        pdokbaggeocoder_status_message(qgis, "Geocoding " + str(recordcount) + " (" + str(notfoundcount) + " not found)")
        total_address = ""
        for x in indices:
            if x < len(row):
                value = row[x].strip()
                value = row[x].replace('-', ' ')
                new_string = urllib.parse.quote(value)

                if len(new_string) > 0:
                    if x != indices[0]:
                        total_address += "+"
                    total_address += new_string

        if len(total_address) <= 0:
            notfoundcount += 1
            notwriter.writerow(row)
        else:
            url_geocoder = 'https://api.pdok.nl/bzk/locatieserver/search/v3_1/free?q='
            url = '{}{}{}&rows=10&bq=type:adres'.format(url_geocoder,total_address, selected_city)
            url_list.append(url)
            try:
                response = urllib.request.urlopen(url).read()
                results = json.loads(response)
                if len(results["response"]["docs"]) > 0:
                    for result in results["response"]["docs"]:
                        if result["score"] == results["response"]["maxScore"]:
                            xy = re.findall(r'\d+\.*\d*', result["centroide_rd"])
                            x = float(xy[0])
                            y = float(xy[1])
                            attributes = []
                            for z in range(0, len(header)):
                                if z < len(row):
                                    attributes.append(row[z].strip())
                            newfeature = QgsFeature()
                            newfeature.setAttributes(attributes)
                            geometry = QgsGeometry.fromPointXY(QgsPointXY(x, y))
                            newfeature.setGeometry(geometry)
                            outfile.addFeature(newfeature)
                            break
                else:
                    notfoundcount += 1
                    notwriter.writerow(row)
                    notfound_list.append(url)
            # website offline?
            except urllib.error.URLError as e:
                end_time = time.time()
                elapsed_time = round(end_time - start_time)
                QMessageBox.critical(qgis.mainWindow(), "Geocoderen met PDOK BAG Geocoder", "Geocoderen mislukt na %s aantal en %s. \n%s \nError\n%s" % (str(recordcount),str(datetime.timedelta(seconds=elapsed_time)),str(url_list[-1]), str(e)))
    del outfile
    del notfound

    end_time = time.time()

    elapsed_time = round(end_time - start_time)

    if addlayer and (recordcount > notfoundcount) and (recordcount > 0):
        vlayer = qgis.addVectorLayer(shapefilename, os.path.basename(shapefilename), "ogr")

    if notfoundcount != 0:
        tips = "\n____________________________________________________________\n\nNiet gevonden locaties:\n" + '\n'.join(map(str, notfound_list[0:])) + "\n\nDe niet gevonden rijen zijn op de volgende locatie opgeslagen:\n" + str(notfoundfile) + "\n"

    else:
        tips=   "\n____________________________________________________________\n\nHieronder zijn de eerste paar gebruikte adressen te zien:\n"+'\n'.join(map(str, url_list[0:5]))+"\n..."

    qgis.mainWindow().statusBar().showMessage(str(recordcount - notfoundcount) + " of " + str(recordcount)
        + " addresses geocoded with PDOK BAG Geocoder")
    QMessageBox.information(qgis.mainWindow(), "Geocoderen met PDOK BAG Geocoder", "%s van %s adressen succesvol gegeocodeerd in %s (in EPSG:28992) \n%s" % ((str(recordcount - notfoundcount)),(str(recordcount)), str(datetime.timedelta(seconds=elapsed_time)),tips))
    return None