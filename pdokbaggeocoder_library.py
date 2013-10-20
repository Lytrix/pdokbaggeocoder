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
import datetime
import urllib
import os.path
import operator
import tempfile
import urllib2
import re
import codecs
#from re import sub


from xml.dom import minidom
from xml.dom.minidom import parseString
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from math import *
import os

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

def pdokbaggeocoder_status_message(qgis, message):
	qgis.mainWindow().statusBar().showMessage(message)


# --------------------------------------------------------------
#    BAG_geocode_pdok - Geocode CSV points from Pdok
# --------------------------------------------------------------


def pdokbaggeocoder(qgis, csvname, shapefilename, notfoundfile, keys, addlayer,current_city, start_time):
	# test value to test all printed weblinks
	global address_list
	address_list=[]
	global value_list
	value_list = []
	global separate_numbers_list
	separate_numbers_list = []
	global onlytext_list
	onlytext_list = []
	global url_list
	url_list = []
	global notfound_list
	notfound_list = []
	global housenumber_list
	housenumber_list = []
	global selected_city_list
	selected_city_list = []
	global tester
	tester = []
	if (not csvname) or (len(csvname) <= 0):
		return "No CSV address file given"	
	# Read the CSV file header
	try:
		infile = open(csvname, 'r')
	except:
		return "Fout bij het openen van " + csvname

	try:
		dialect = csv.Sniffer().sniff(infile.readline(), [',',';',';','|'],)
	except:
		return "Fout bij het openen van " + unicode(csvname) + ": " + unicode(sys.exc_info()[1]) + "Controleer of de scheidingstekens consistent zijn gekozen en deze niet in de velden voorkomen."

	
	fields = QgsFields()
	indices = []
	# if city selected from list then use this field
	if current_city != "":
		selected_city = "+" + urllib.quote(current_city)
		selected_city_list.append(selected_city)
	else:
		selected_city=""
	
	try:
		infile.seek(0)
		reader = csv.reader(infile, dialect)
		header = reader.next()
	except:
		return "Fout bij het lezen van " + unicode(csvname) + ": " + unicode(sys.exc_info()[1])

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
			return "Kan shapefile: " + unicode(shapefilename) + "niet openen."

	crs = QgsCoordinateReferenceSystem()
	crs.createFromSrid(28992)
	outfile = QgsVectorFileWriter(shapefilename, "System", fields, QGis.WKBPoint, crs)

	if (outfile.hasError() != QgsVectorFileWriter.NoError):
		return "Schrijffout bij het aanmaken van de shapefile: " + unicode(outfile.errorMessage())

	# Geocode and import

	recordcount = 0
	notfoundcount = 0
	for row in reader:
		recordcount += 1	
		pdokbaggeocoder_status_message(qgis, "Geocoding " + unicode(recordcount) + 
			" (" + unicode(notfoundcount) + " not found)")		
		#time.sleep(1) # to avoid pdok.nl quota limits
		total_address = ""
		
		for x in indices:
			if x < len(row):
				value = row[x].strip().replace('-',' ')
				#value = row[x].strip().replace(" ","+")
				#value = urllib.quote(row[x].strip()
				
				pc_turn = [p for p in row if row[x][0:3].isdigit()]
				#tester.append(pc_turn)
				if pc_turn != []:
					new_string = value.replace(' ','')	
				else:
					# put (house)numbers in seperate list
					separate_numbers=[n for n in value.split() if n.isdigit()]
					#separate_numbers_list.append(separate_numbers)
					# put a-z words in another
					#only_text = [a for a in value.split() if a.isalpha()]
					
					# put all words in a list
					total_text = [i for i in value.split() if not i.isdigit()]
					
					# list with to be removed listed items
					letter_extensions = ['HS','H','I','II','III','IV','V','VI','VII','VIII','IX','X','A','B','C','D','E','F','G',',',':']
					# list with removed items
				
					separate_text = [t for t in total_text if t not in letter_extensions]
				
					# join words back together with space
					only_text = ' '.join(separate_text)
				
					# if numbers are present select only first one
					if separate_numbers:
						housenumber_selection= "+" + separate_numbers[0]
						#housenumber_list.append(housenumber_selection) 
					else:
						housenumber_selection=""
					# join name and number (if street name is present)
					new_string = urllib.quote(only_text) + housenumber_selection
				
								
				if len(new_string) > 0:
					if x != indices[0]:	
						total_address += "+"
					total_address += new_string
					
				# checks of listed outputs in message box	
				#value_list.append(value)
				#separate_numbers_list.append(separate_numbers)
				#onlytext_list.append(separate_text)
				#address_list.append(new_string)
				
		if len(total_address) <= 0:
			notfoundcount += 1
			notwriter.writerow(row)
			
		else:
			try:
				url = "http://geodata.nationaalgeoregister.nl/geocoder/Geocoder?zoekterm=" + total_address + selected_city
					
				# test output to print all weblinks
				url_list.append(url)
				try:
					xml = urllib2.urlopen(url).read()
					doc = parseString(xml)
					xmlTag = doc.getElementsByTagName("gml:pos")[0].firstChild.nodeValue								
					# if total_address is correctly written xmlTag exists:
					if xmlTag:	
						remark=True
						# split X and Y coordinate in list
						XY = xmlTag.split()
						if XY:
							x = float(XY[0])
							y = float(XY[1])
							print "%s" % x
							print "%s" % y
							# print address + ": " + str(x) + ", " + str(y)
						attributes = []
						for z in range(0, len(header)):
							if z < len(row):
								attributes.append(unicode(row[z], 'utf-8').strip())

						newfeature = QgsFeature()
						newfeature.setAttributes(attributes)
						geometry = QgsGeometry.fromPoint(QgsPoint(x, y))
						newfeature.setGeometry(geometry)
						outfile.addFeature(newfeature)
				except:
					notfoundcount += 1
					notwriter.writerow(row)
					notfound_list.append(url)
			# website offline?
			except:
				end_time = time.time()
				elapsed_time = round(end_time - start_time)
				QMessageBox.critical(qgis.mainWindow(),"Geocoderen met PDOK BAG Geocoder" ,"Geocoderen mislukt na %s aantal en %s. \n%s" % (unicode(recordcount),str(datetime.timedelta(seconds=elapsed_time)),unicode(url_list[-1])))
	#			return
	del outfile
	del notfound
	

	end_time = time.time()

	elapsed_time = round(end_time - start_time)
		
	if addlayer and (recordcount > notfoundcount) and (recordcount > 0):
		vlayer = qgis.addVectorLayer(shapefilename, os.path.basename(shapefilename), "ogr")
	
	if notfoundcount != 0:
		tips = "\n____________________________________________________________\n\nNiet gevonden locaties:\n" + '\n'.join(map(str, notfound_list[0:])) + "\n\nDe niet gevonden rijen zijn op de volgende locatie opgeslagen:\n" + unicode(notfoundfile) + "\n"
		
	else:
		tips=	"\n____________________________________________________________\n\nHieronder zijn de eerste paar gebruikte adressen te zien:\n"+'\n'.join(map(str, url_list[0:5]))+"\n..."

	
	qgis.mainWindow().statusBar().showMessage(unicode(recordcount - notfoundcount) + " of " + unicode(recordcount)
		+ " addresses geocoded with PDOK BAG Geocoder")
	QMessageBox.information(qgis.mainWindow(), "Geocoderen met PDOK BAG Geocoder", "%s van %s adressen succesvol gegeocodeerd in %s (in EPSG:28992) \n%s" % ((unicode(recordcount - notfoundcount)),(unicode(recordcount)), str(datetime.timedelta(seconds=elapsed_time)),tips))
	return None