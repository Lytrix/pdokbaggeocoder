PDOK BAG geocoder
=================
.. image:: https://img.shields.io/badge/python-2.7-blue.svg
   :target: https://www.python.org/

.. image:: https://img.shields.io/badge/license-MPLv2.0-blue.svg
   :target: https://www.mozilla.org/en-US/MPL/2.0/


PDOK BAG geocoder is a QGIS plugin for finding Dutch XY coordinates from a CSV file with addresses with use of the National BAG geocoder webservice.

Usage
=====
The PDOK BAG geocoder is designed to add xy coordinates to a simple table of  address with your own attributes. The National Dutch address dataset will be used called the BAG. 

BAG stands for: The Municipal records of Addresses and Buildings 
"Basisregistratie Adressen en Gebouwen" in Dutch.

The file will be saved as a shapefile to be reused and edited in QGIS.

Addresses which were not found with the geocoding service, are saved in a _niet_gevonden.csv file to examine and review. You can edit the source file to import the file again and overwrite the shapefile.


Credits
=======

This plugin is based on framework of the 
MMQGIS Geocode CSV with Google plugin created by Michael Minn. 
Go to http://plugins.qgis.org/plugins/mmqgis/ for more information.
	
The geocoding is provided by the www.pdok.nl geocoding webservice:
Go to https://www.pdok.nl/nl/producten/pdok-locatieserver for more information.

The csv file of cities list cities who are participating with the BAG transition. Go to http://www.kadaster.nl/web/Themas/themaartikel/BAGartikel/BAG-woonplaatscodetabel.htm for the source file.


Issues
======
For bugs please add an issue here with an example file or screenshot:

https://github.com/Lytrix/pdokbaggeocoder/issues