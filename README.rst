PDOK BAG Excel to CSV coordinate finder
=======================================
.. image:: https://img.shields.io/badge/python-2.7-blue.svg
   :target: https://www.python.org/

.. image:: https://img.shields.io/badge/license-MPLv2.0-blue.svg
   :target: https://www.mozilla.org/en-US/MPL/2.0/


This Python script finds Dutch XY coordinates from an Excel file using the [National BAG geocoder REST API service](https://www.pdok.nl/nl/producten/pdok-locatieserver) and returns 2 csv files with found and not found locations.

Usage
=====
The PDOK BAG geocoder script is designed to add xy coordinates to a simple table of addresses with your own attributes. 

The National Dutch address dataset will be used called the BAG. 
BAG stands for: The Municipal records of Addresses and Buildings 
"Basisregistratie Adressen en Gebouwen" in Dutch.

The script assumes the first row contains the header with a column named adres or address and postcode, city. 
The file will be saved as a csv to be reused for example in QGIS.

Addresses which were not found with the geocoding service, are saved in a _not_found.csv file to examine and review. You can edit the source file to import the file again and overwrite the shapefile.

Example command line:
	``python bag_geocode.py testdata/nomatch.xlsx --city Amsterdam``

    Args:
        1. filename: some_folder/your_file.xls
        2. --city: Amsterdam, is optional, it will search for a column named: 'stad', 'city', 'woonplaats', 'plaats'
    Returns:
        A CSV file of the XLS with BAG id, coordinates and naming.

Credits
=======
	
The geocoding is provided by the www.pdok.nl geocoding webservice:
Go to https://www.pdok.nl/nl/producten/pdok-locatieserver for more information.


Issues
======
For bugs please add an issue here with the steps you took and an example file and/or screenshot:

https://github.com/Lytrix/pdokbaggeocoder/issues
