# --------------------------------------------------------
#    __init__ - PDOK BAG Geocoder init file
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
#http://www.kadaster.nl/web/Themas/themaartikel/BAGartikel/BAG-woonplaatscodetabel.htm
#	for the source file.
#
#   The BAG geocoder is free software and is offered without guarantee
#   or warranty. You can redistribute it and/or modify it 
#   under the terms of version 2 of the GNU General Public 
#   License (GPL v2) as published by the Free Software 
#   Foundation (www.gnu.org).
# --------------------------------------------------------


from pdokbaggeocoder_menu import pdokbaggeocoder_menu

def name():
	return "PDOK BAG Geocoder"
def description():
	return "Get X,Y coordinates in EPSG:28992 with the PDOK geocoding webservice"
def version():
	return "0.2"
def icon():
	return "icon.png"
def qgisMinimumVersion():
	return "1.8"
def author():
	return "Eelke Jager"
def email():
	return "info@lytrix.com"
def category():
  return "Vector"
def classFactory(iface):
	return pdokbaggeocoder_menu(iface)
