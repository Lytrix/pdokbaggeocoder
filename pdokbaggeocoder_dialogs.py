# --------------------------------------------------------
#    pdokbaggeocoder_dialogs - Dialog classes for pdokbaggeocoder
#
#    begin		          : 1 May 2013
#    copyright            : (c) 2013 by Eelke Jager
#    e-Mail               : info [at] lytrix.com
#
#	This plugin is based on framework of the 
#	MMQGIS Geocode CSV with Google plugin created by Michael Minn. 
#	Go to 
#	http://plugins.qgis.org/plugins/mmqgis/ for more information.
#	
#	The geocoding is provided by the www.pdok.nl geocoding webservice:
#	Go to 
#	https://www.pdok.nl/nl/service/openls-bag-geocodeerservice 
#	for more information.
#
#	The city list who are participating with the BAG transition 
#	are provided by the www.kadaster.nl
# 	Go to 
#	http://www.kadaster.nl/web/Themas/themaartikel/BAGartikel/BAG-woonplaatscodetabel.htm
#	for the source file.
#
#   The BAG geocoder is free software and is offered without guarantee
#   or warranty. You can redistribute it and/or modify it 
#   under the terms of version 2 of the GNU General Public 
#   License (GPL v2) as published by the Free Software 
#   Foundation (www.gnu.org).
# --------------------------------------------------------

import csv
import os.path
import operator
import webbrowser

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis import core
from pdokbaggeocoder_library import *

import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/forms")



# --------------------------------------------------------
#    pdokbaggeocoder - Geocode using BAG data from PDOK
# --------------------------------------------------------

from pdokbaggeocoder_form import *

class pdokbaggeocoder_dialog(QDialog, Ui_pdokbaggeocoder_form):
	
	# storage container of header names for self.city
	global stored
	stored = ''	
			
	def __init__(self, iface):
		QDialog.__init__(self)
		self.setupUi(self)
		self.iface = iface
                self.notfoundfilename.hide()
		QObject.connect(self.browse_infile, SIGNAL("clicked()"), self.browse_infile_dialog)
		QtCore.QObject.connect(self.radio_list,QtCore.SIGNAL("toggled(bool)"), self.radio_activateInput)
		QtCore.QObject.connect(self.radio_column,QtCore.SIGNAL("toggled(bool)"), self.radio_activateInput)
		self.radio_column.setChecked(True)
		QObject.connect(self.browse_shapefile, SIGNAL("clicked()"), self.browse_shapefile_dialog)
		#QObject.connect(self.help_button, SIGNAL("clicked()"), self.open_help)
		#QObject.connect(self.browse_notfound, SIGNAL("clicked()"), self.browse_notfound_dialog)
		QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), self.run)
		self.distinct
		global stored
		stored = ''
		self.city.clear()
	
	def open_help(self):
		dir = QFileInfo(core.QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/pdokbaggeocoder"
		webbrowser.open(dir + "README.txt")


	def browse_infile_dialog(self):
		newname = QFileDialog.getOpenFileName(None, "Address CSV Input File", 
			self.infilename.displayText(), "CSV File (*.csv *.txt)")
		if newname:
			try:
				infile = open(newname, 'r')
				dialect = csv.Sniffer().sniff(infile.readline(), [',',';',';','|'])
			except:
				QMessageBox.critical(self.iface.mainWindow(), "Geocoderen met PDOK BAG Geocoder", \
					newname + " inaccessible or in unrecognized CSV format: " + unicode(sys.exc_info()[1]))
				return

			if len(newname) > 4:
				prefix = newname[:len(newname) - 4]
				self.shapefilename.setText(prefix + ".shp")
				self.notfoundfilename.setText(prefix + "_notfound.csv")
			else:
				self.shapefilename.setText(os.getcwd() + "/geocoded.shp")
				self.notfoundfilename.setText(os.getcwd() + "/notfound.csv")

			infile.seek(0)
			try:
				reader = csv.reader(infile, dialect)
				header = reader.next()
			except:
				QMessageBox.critical(self.iface.mainWindow(), "Geocoderen met PDOK BAG Geocoder", \
					newname + " inaccessible or in unrecognized CSV format: " + unicode(sys.exc_info()[1]))
				return

			del reader
			
			combolist = [self.address, self.housenumber, self.city]
			for box in combolist:
				box.clear()
				box.addItem("----")
				box.setCurrentIndex(0)	
			for index in range(0, len(header)):
				field = header[index]
				for box in combolist:	
					box.addItem((field))
				# preselect value if name is found
				if field.lower().find("adres") >= 0:
					self.address.setCurrentIndex(index + 1)
				if field.lower().find("addr") >= 0:
					self.address.setCurrentIndex(index + 1)
				if field.lower().find("locatie") >= 0:
					self.address.setCurrentIndex(index + 1)
				if field.lower().find("location") >= 0:
					self.address.setCurrentIndex(index + 1)
				if field.lower().find("straat") >= 0:
					self.address.setCurrentIndex(index + 1)
				if field.lower().find("street") >= 0:
					self.address.setCurrentIndex(index + 1)				
				if field.lower().find("housenumber") >= 0:
					self.housenumber.setCurrentIndex(index + 1)
				if field.lower().find("huisnummer") >= 0:
					self.housenumber.setCurrentIndex(index + 1)					
				if field.lower() == "huisnr":
					self.housenumber.setCurrentIndex(index + 1)
				if field.lower() == "nr":
					self.housenumber.setCurrentIndex(index + 1)
				if field.lower().find("city") >= 0:
					self.radio_column.setChecked(True)
					self.city.setCurrentIndex(index + 1)
				if field.lower().find("stad") >= 0:
					self.radio_column.setChecked(True)
					self.city.setCurrentIndex(index + 1)
				if field.lower().find("plaats") >= 0:
					self.radio_column.setChecked(True)
					self.city.setCurrentIndex(index + 1)
				if field.lower().find("woonplaats") >= 0:
					self.radio_column.setChecked(True)
					self.city.setCurrentIndex(index + 1)	
				self.infilename.setText(newname)
			
			# store header names for self.city usage		
			def save_column_list(input):
				try:
					return input()
				except TypeError:
					return input
			# execute storage of header names
			global stored		
			stored = save_column_list(header)
			
	def browse_notfound_dialog(self):
		newname = QFileDialog.getSaveFileName(None, "Not Found List Output File", 
			self.notfoundfilename.displayText(), "CSV File (*.csv *.txt)")
                if newname != None:
                	self.notfoundfilename.setText(newname)

	def browse_shapefile_dialog(self):
		newname = QFileDialog.getSaveFileName(None, "Output Shapefile", 
			self.shapefilename.displayText(), "*.shp")
                if newname != None:
                	self.shapefilename.setText(newname)
	
	# distinct function to cleanup city csv file
	def distinct(self,list):	
		seen = set()
		seen_add = seen.add
		return [ x for x in list if x not in seen and not seen_add(x)]
    
    # action when radio_button is clicked
	def radio_activateInput(self):
		if self.radio_list.isChecked():
			# load cities
			def get_col(filename, col=0):
				dir = QFileInfo(core.QgsApplication.qgisUserDbFilePath()).path() + "/python/plugins/pdokbaggeocoder"
				for row in csv.reader(open(dir + "/14-02-2013 WPL overzicht gemeenten.csv"), delimiter=';'):
					if row != 0:
						if row[col] is not '':
							yield row[col]
			cities=list(get_col("woonplaats"))
			# get only distinct city names
			distinct_cities=self.distinct(cities)
			#print "%s" %  cities
			self.city.clear()
			self.city.addItem("Kies woonplaats")
			self.city.addItems(distinct_cities)
			# start with Amsterdam
			self.city.setCurrentIndex(0)
	
		if self.radio_column.isChecked(): 
			# reset box
			self.city.clear()
			# if storage is filled
			if stored != '':
				# add headers and a ---- option, start with ----			
				self.city.addItem("----")
				self.city.setCurrentIndex(0)	
				
				for index in range(0, len(stored)):
					field = stored[index]
					self.city.addItem(field)
					# preselect value if name is found
					if field.lower().find("city") >= 0:
						self.city.setCurrentIndex(index + 1)
					if field.lower().find("stad") >= 0:
						self.city.setCurrentIndex(index + 1)
					if field.lower().find("plaats") >= 0:
						self.city.setCurrentIndex(index + 1)
					if field.lower().find("city") >= 0:
						self.city.setCurrentIndex(index + 1)	
			
	def run(self):
		
		start_time = time.time()
		
		# alert if no city is given
		csvname = unicode(self.infilename.displayText()).strip()
		shapefilename = unicode(self.shapefilename.displayText())
		notfoundfile = self.notfoundfilename.displayText()
		test = self.city.currentIndex()
			
		if test == 0:
			QMessageBox.critical(self.iface.mainWindow(), "PDOK BAG Geocoder", "Geen Woonplaats kolom ingevuld!")
			# use - instead of + for extension and letter additions in search sentence
			#if self.housenumber_extension or self.housenumber_letter:
			#	dash="-"
			#else:
			#	dash=""
		else:
			if self.radio_list.isChecked():
				# separate field for single cityname
				current_city=unicode(self.city.currentText())
				fields = [unicode(self.address.currentText()).strip(), unicode(self.housenumber.currentText()).strip()]
		
			if self.radio_column.isChecked():
			# create address search line: address+housenumber-extension or letter+city	
				current_city=""
				fields = [unicode(self.address.currentText()).strip(), unicode(self.housenumber.currentText()).strip(),unicode(self.city.currentText()).strip()]
		
			for x in range(0, len(fields)):
				if fields[x] == "----":
					fields[x] = ""		
	
			# print csvname + "," + "," + shapefilename
			message = pdokbaggeocoder(self.iface, csvname, shapefilename, notfoundfile, fields, 1, current_city, start_time)
			if message <> None:
				QMessageBox.critical(self.iface.mainWindow(), "Geocode BAG", message)	
