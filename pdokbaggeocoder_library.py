# --------------------------------------------------------
#    __init__ - BAG geocoder init file
#
#    creation date        : 1 May 2013
#    copyright            : (c) 2013 by Eelke Jager
#    e-Mail               : info [at] lytrix.com
#
#	This plugin is based on framework of the 
#	MMQGIS Geocode CSV with Google plugin created by Michael Minn. 
#	Go to http://plugins.qgis.org/plugins/mmqgis/ for more information.
#	
#	The geocoding is provided by the www.pdok.nl geocoding webservice:
#	Go to https://www.pdok.nl/nl/service/openls-bag-geocodeerservice 
#	for more information.
#
#   The BAG geocoder is free software and is offered without guarantee
#   or warranty. You can redistribute it and/or modify it 
#   under the terms of version 2 of the GNU General Public 
#   License (GPL v2) as published by the Free Software 
#   Foundation (www.gnu.org).
# --------------------------------------------------------

import csv
import sys
import time
import urllib
import os.path
import operator
import tempfile
import urllib2

from xml.dom import minidom
from xml.dom.minidom import parseString
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from math import *

# --------------------------------------------------------
#    BAG geocoder Functions
# --------------------------------------------------------

def pdokbaggeocoder_find_layer(layer_name):
	# print "find_layer(" + str(layer_name) + ")"

	for name, search_layer in QgsMapLayerRegistry.instance().mapLayers().iteritems():
		if search_layer.name() == layer_name:
			return search_layer

	return None

def pdokbaggeocoder_is_float(s):
	try:
		float(s)
		return True
	except:
		return False

# Cumbersome function to give backward compatibility before python 2.7

def format_float(value, separator, decimals):
	formatstring = ("%0." + unicode(int(decimals)) + "f")
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


# baggeocoder_layer_attribute_bounds() is needed because the 
# QgsVectorDataProvider::minimumValue() and maximumValue() 
# do not work as of QGIS v1.5.0

def pdokbaggeocoder_layer_attribute_bounds(layer, attribute_name):
	#attribute_index = -1
	#for index, field in layer.dataProvider().fields().iteritems():	
	#	if str(field.name()) == attribute_name:
	#		attribute_index = index

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
	if wkbtype == QGis.WKBUnknown: return "Unknown"
	if wkbtype == QGis.WKBPoint: return "point"
	if wkbtype == QGis.WKBLineString: return "linestring"
	if wkbtype == QGis.WKBPolygon: return "polygon"
	if wkbtype == QGis.WKBMultiPoint: return "multipoint"
	if wkbtype == QGis.WKBMultiLineString: return "multilinestring"
	if wkbtype == QGis.WKBMultiPolygon: return "multipolygon"
	# if wkbtype == QGis.WKBNoGeometry: return "no geometry"
	if wkbtype == QGis.WKBPoint25D: return "point 2.5d"
	if wkbtype == QGis.WKBLineString25D: return "linestring 2.5D"
	if wkbtype == QGis.WKBPolygon25D: return "multipolygon 2.5D"
	if wkbtype == QGis.WKBMultiPoint25D: return "multipoint 2.5D"
	if wkbtype == QGis.WKBMultiLineString25D: return "multilinestring 2.5D"
	if wkbtype == QGis.WKBMultiPolygon25D: return "multipolygon 2.5D"
	return "Unknown WKB " + unicode(wkbtype)




# --------------------------------------------------------------
#    BAG_geocode_pdok - Geocode CSV points from Pdok
# --------------------------------------------------------------

def pdokbaggeocoder(qgis, csvname, shapefilename, notfoundfile, keys, addlayer):
	# Read the CSV file header
	try:
		infile = open(csvname, 'r')
	except:
		return "Failure opening " + csvname

	try:
		dialect = csv.Sniffer().sniff(infile.read(2048))
	except:
		return "Failure reading " + unicode(csvname) + ": " + unicode(sys.exc_info()[1])


	fields = {}
	indices = []
	try:
		infile.seek(0)
		reader = csv.reader(infile, dialect)
		header = reader.next()
	except:
		return "Failure reading " + unicode(csvname) + ": " + unicode(sys.exc_info()[1])

	for x in range(0, len(header)):
		for y in range(0, len(keys)):
			if header[x] == keys[y]:
				indices.append(x)

		fieldname = header[x].strip()
		fields[len(fields)] = QgsField(fieldname[0:9], QVariant.String)

	if (len(fields) <= 0) or (len(indices) <= 0):
		return "No valid location fields in " + csvname


	# Create the CSV file for ungeocoded records
	try:
		notfound = open(notfoundfile, 'w')
	except:
		return "Failure opening " + notfoundfile

	notwriter = csv.writer(notfound, dialect)
	notwriter.writerow(header)


	# Create the output shapefile
	if QFile(shapefilename).exists():
		if not QgsVectorFileWriter.deleteShapeFile(QString(shapefilename)):
			return "Failure deleting existing shapefile: " + unicode(shapefilename)

	crs = QgsCoordinateReferenceSystem()
	crs.createFromSrid(28992)
	outfile = QgsVectorFileWriter(QString(shapefilename), QString("System"), fields, QGis.WKBPoint, crs)

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Failure creating output shapefile: " + unicode(outfile.errorMessage())

	# Geocode and import

	recordcount = 0
	notfoundcount = 0
	for row in reader:
		recordcount += 1	

		qgis.mainWindow().statusBar().showMessage("Geocoding " + unicode(recordcount) + 
			" (" + unicode(notfoundcount) + " not found)")
		time.sleep(1) # to avoid pdok.nl quota limits
		address = ""
		for x in indices:
			if x < len(row):
				# value = row[x].strip().replace(" ","+")
				value = urllib.quote(row[x].strip())
				if len(value) > 0:
					if x != indices[0]:
						address += "+"
					address += value

		if len(address) <= 0:
			notfoundcount += 1
			notwriter.writerow(row)
	
		else:
			try:
				url = "http://geodata.nationaalgeoregister.nl/geocoder/Geocoder?zoekterm=" + address
				xml = urllib2.urlopen(url).read()
				#get the first xml tag (<tag>data</tag>) that the parser finds with name gml:
				dom = minidom.parse(urllib2.urlopen(url))

				doc = parseString(xml)
				if doc.getElementsByTagName('gml:pos'):
					xmlTag = doc.getElementsByTagName('gml:pos')[0].firstChild.nodeValue								
					# split X and Y coordinate in list
					XY = xmlTag.split()
					if XY:
						x = float(XY[0])
						y = float(XY[1])
						print "%s" % x
						print "%s" % y
						# print address + ": " + str(x) + ", " + str(y)
						attributes = {}
					for z in range(0, len(header)):
						if z < len(row):
							attributes[z] = QVariant(row[z].strip())
					newfeature = QgsFeature()
					newfeature.setAttributeMap(attributes)
					geometry = QgsGeometry.fromPoint(QgsPoint(x, y))
					newfeature.setGeometry(geometry)
					outfile.addFeature(newfeature)
				else:
					notfoundcount += 1
					notwriter.writerow(row)
					# print xml
			except:
				QMessageBox.critical(qgis.mainWindow(),"Geocoderen met PDOK BAG Geocoder" ,"Geocoderen mislukt. De geocodeer service van PDOK is momenteel niet bereikbaar. \n\nProbeer het later nog een keer of kijk voor de status van de storing bij de meldingen op www.pdok.nl.")
				return None
	del outfile
	del notfound

	if addlayer and (recordcount > notfoundcount) and (recordcount > 0):
		vlayer = qgis.addVectorLayer(shapefilename, os.path.basename(shapefilename), "ogr")
		
	qgis.mainWindow().statusBar().showMessage(unicode(recordcount - notfoundcount) + " of " + unicode(recordcount)
		+ " addresses geocoded with PDOK BAG Geocoder")
	QMessageBox.information(qgis.mainWindow(), "Geocoderen met PDOK BAG Geocoder", unicode(recordcount - notfoundcount) + " of " + unicode(recordcount)
		+ " adressen succesvol gegeocodeerd in EPSG:28992.\n\n Kijk in het onderstaande bestand:\n"+unicode(notfoundfile)+" \nvoor de niet gevonden locaties.\n_______________________________________________________\nAls er geen locaties gevonden zijn, controleer of het huisnummer bestaat, of het gebruik van ij of y, ck correct is volgens de BAG.\nOf gebruik, indien beschikbaar, de postcodes voor een globale plaatsbepaling van de locaties.")
	return None