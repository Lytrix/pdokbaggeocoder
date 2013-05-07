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

from pdokbaggeocoder_dialogs import *

# ---------------------------------------------

class pdokbaggeocoder_menu:
	def __init__(self, iface):
		self.iface = iface

	def initGui(self):
  		# Create action
    		icon = QIcon(os.path.dirname(__file__) + "/icon.png")
    		self.action = QAction(QIcon(icon),"PDOK BAG Geocoder",self.iface.mainWindow())
    		self.action.setWhatsThis("BAG geocoder with the PDOK webservice")
    		QObject.connect(self.action,SIGNAL("triggered()"),self.run)
    		self.iface.addToolBarIcon(self.action)
    		self.iface.addPluginToMenu("&PDOK Bag Geocoder",self.action)
    		# self.about = QAction("About ImportProject",self.iface.mainWindow())
    		#QObject.connect(self.about,SIGNAL("triggered()"),self.clickAbout)
    		#self.iface.addPluginToMenu("&BagGeocoder",self.about)


  	def unload(self):
	# Remove the plugin
		self.iface.removePluginMenu("&PDOK Bag Geocoder",self.action)
		self.iface.removeToolBarIcon(self.action)

  	def run(self):
		dialog = pdokbaggeocoder_dialog(self.iface)
		dialog.exec_()

