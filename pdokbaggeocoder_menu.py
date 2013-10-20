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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from pdokbaggeocoder_dialogs import pdokbaggeocoder_dialog
import os.path
# ---------------------------------------------

class pdokbaggeocoder_menu:

	def __init__(self, iface):
		# Save reference to the QGIS interface
		self.iface = iface
		# Create the dialog (after translation) and keep reference
		self.dlg = pdokbaggeocoder_dialog(iface)

	def initGui(self):
		icon = QIcon(os.path.dirname(__file__) + "/icon.png")
		self.action = QAction(icon, "PDOK BAG Geocoder", self.iface.mainWindow())
		self.action.triggered.connect(self.run)
		# Add toolbar button and menu item
		self.iface.addToolBarIcon(self.action)
		self.iface.addPluginToMenu(u"&PDOK BAG Geocoder", self.action)
		
	def unload(self):
		# Remove the plugin menu item and icon
		self.iface.removePluginMenu(u"&PDOK BAG Geocoder", self.action)
		self.iface.removeToolBarIcon(self.action)
		  
	# run method that performs all the real work	
	def run(self):
		# show the dialog
		self.dlg.show()
		# Run the dialog event loop
		result = self.dlg.exec_()
		# See if OK was pressed
		if result == 1:
			pass