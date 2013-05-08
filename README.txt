PDOK BAG geocoder
--------------------------------------------------------

The PDOK BAG geocoder is designed to add xy coordinates to a simple table of  address with your own attributes. The National Dutch address dataset will be used called the BAG. 

BAG stands for: The Municipal records of Addresses and Buildings 
"Basisregistratie Adressen en Gebouwen" in Dutch.

The file will be saved as a shapefile to be reused and edited in QGIS.

Addresses which were not found with the geocoding service, are saved in a _niet_gevonden.csv file to examine and review. You can edit the source file to import the file again and overwrite the shapefile.


--------------------------------------------------------
begin		          : 1 May 2013
copyright            : (c) 2013 by Eelke Jager
e-Mail               : info [at] lytrix.com

This plugin is based on framework of the 
MMQGIS Geocode CSV with Google plugin created by Michael Minn. 
Go to http://plugins.qgis.org/plugins/mmqgis/ for more information.
	
The geocoding is provided by the www.pdok.nl geocoding webservice:
Go to https://www.pdok.nl/nl/service/openls-bag-geocodeerservice for more information.

The city list who are participating with the BAG transition 
are provided by the www.kadaster.nl
Go to http://www.kadaster.nl/web/Themas/themaartikel/BAGartikel/BAG-woonplaatscodetabel.htm for the source file.
--------------------------------------------------------
The BAG geocoder is free software and is offered without guarantee or warranty. You can redistribute it and/or modify it under the terms of version 2 of the GNU General Public License (GPL v2) as published by the Free Software Foundation (www.gnu.org).
--------------------------------------------------------

The source code can be found at:

https://github.com/Lytrix/pdokbaggeocoder

For bugreports please visit:

https://github.com/Lytrix/pdokbaggeocoder/issues