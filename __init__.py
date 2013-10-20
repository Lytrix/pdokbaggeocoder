# -*- coding: utf-8 -*-
"""
/***************************************************************************
 pdokbaggeocoder
                                 A QGIS plugin
 Get X,Y coordinates in EPSG:28992 with the PDOK geocoding webservice
                             -------------------
        begin                : 2013-10-11
        copyright            : (C) 2013 by Lytrix
        email                : info@lytrix.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


def name():
	return "PDOK BAG Geocoder"

def description():
	return "Get X,Y coordinates in EPSG:28992 with the PDOK geocoding webservice"

def version():
	return "Version 0.5"

def icon():
	return "icon.png"

def qgisMinimumVersion():
	return "2.0"

def author():
	return "Lytrix"

def email():
	return "info@lytrix.com"

def classFactory(iface):
	# load pdokbaggeocoder class from file pdokbaggeocoder
	from pdokbaggeocoder_menu import pdokbaggeocoder_menu
	return pdokbaggeocoder_menu(iface)
