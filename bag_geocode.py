import os
import csv
import json
import xlrd
import requests
import requests_cache
import argparse
import re


def parser():
    """
    Parser function to run arguments from commandline and to add description to sphinx docs.
    To see possible styling options: https://pythonhosted.org/an_example_pypi_project/sphinx.html
    """
    description = """
    Use PDOK API to clean addresses. and returns the CSV.
    Example command line:
        ``geocode_xls_to_csv tests/transform/testdata/bag_geocoding.xlsx --city Amsterdam``
    Args:
        1. filename: some_folder/your_file.xls
        2. --city: Amsterdam, is optional, it will search for a column named: 'stad', 'city', 'woonplaats', 'plaats'
    Returns:
        A CSV file of the XLS with BAG id, coordinates and naming.
    """

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('filename',
                        type=str,
                        help='Add filename')
    parser.add_argument('--city', type=str, help='Add city name if there is no column provided')
    return parser


def loadSheet(file, sheet_number=0, header=True):
    workbook = xlrd.open_workbook(file)
    sheet_names = workbook.sheet_names()
    print(sheet_names)
    worksheet = workbook.sheet_by_index(sheet_number)
    data = []
    if header:
        first_row = [] # The row where we stock the name of the column
        for col in range(worksheet.ncols):
            first_row.append( worksheet.cell_value(0,col) )
    for row in range(1, worksheet.nrows):
        elm = {}
        for col in range(worksheet.ncols):
            value = worksheet.cell_value(row,col)
            # fix float excel issue
            if type(value) == float:
                value = int(value)
            elm[first_row[col]] = value
        data.append(elm)
    print(data)
    return data


def findColumns(data):
    # Key names
    first_row = []
    city_titles = [
        'stad',
        'city',
        'woonplaats',
        'plaats']
    street_titles = [
        'adres',
        'address',
        'straat',
        'straatnaam',
        'weg',
        'addresses',
        'locatie']
    zipcode_titles = [
        'postcode',
        'pc',
        'pc6',
        'pc4',
        'pc5',
        'zipcode',
        'zip']
    housenumber_titles = [
        'huisnummer',
        'nummer',
        'huisnr.',
        'nr',
        'nr.',
        'house number',
        'housenumber']

    columns = {
        "address_column": '',
        "housenumber_column": '',
        "zipcode_column": '',
        "city_column": ''}

    for key in data[0].keys():
        if key.lower() in city_titles:
            columns["city_column"] = key
        if key.lower() in street_titles:
            columns["address_column"] = key
        if key.lower() in zipcode_titles:
            columns["zipcode_column"] = key
        if key.lower() in housenumber_titles:
            columns["housenumber_column"] = key
    return columns


def cleanAddress(address):
    cleaningsteps = [
        r'.*;',
        r'[+.]',
        r'[I]{1,3}$',
        r'[-/][A-Z0-9]*$',
        r'hg$']
    for cleaningstep in cleaningsteps:
        address = re.sub(cleaningstep, '', address)

    cleanAdditions = [r'hs$',r'huis$']
    for cleanAddition in cleanAdditions:
        address = re.sub(cleanAddition, '-H', address, flags=re.IGNORECASE)

    address = re.sub(r'  ', ' ', address)
    return address


def search(address, zipcode, housenumber, city, sort_type):
    """
    Args:
    - type: adres, woonplaats
    """
    url = 'http://geodata.nationaalgeoregister.nl/locatieserver/free?q='
    query_string = " ".join((address, zipcode, str(housenumber), city))
    print('requesting: {}{}'.format(url, query_string))

    url = requests.get(url + query_string +'&bq=type:'+sort_type)
    result = json.loads(url.text)
    print(result)
    return result


def getAddress(item, columns, city=None):
    #if postcodeCell == '0000AA' or re.match(r'^[0-9.]+$', postcodeCell) or re.match(r'^[2-9]{1}', postcodeCell):
    #    print('TRUE')
    #    postcodeCell = ''
    #else:
    #    postcodeCell = str(worksheet.cell_value(row, 2)).strip()

    address = str(item[columns["address_column"]]).strip()

    housenumber = item[columns["housenumber_column"]]
    if housenumber is not '':
        housenumber = str(int(housenumber))
    pc6 = re.match(r'(\d{4}\s*[A-Z]{2})', address)
    if pc6:
        zipcode = pc6.group(1)
    else:
        zipcode = item[columns["zipcode_column"]]
    if not city:
        city = item[columns["city_column"]].strip()
    result = search(address, zipcode, housenumber, city, 'adres')

    init_data = {
        "Woonplaats": '',
        "Postcode BAG": '',
        "Straatnaam BAG": '',
        "Huisnummer BAG": '',
        "Woonplaats BAG": '',
        "wkt_latlon": "POINT(0 0)",
        "wkt_rd": "POINT(0 0)",
        "lat": 0,
        "lon": 0,
        "nummeraanduiding_id": '',
        "Matching": ''
    }
    item.update(init_data)
    print(item)

    resultBAG = result["response"]["docs"][0]
    # print(resultBAG)
    if result["response"]["maxScore"] < 5:
        item["Matching"] = 'Onvoldoende locatie gegevens om een locatie te vinden'
    elif not resultBAG.get("postcode"):
        result = search(address, zipcode, housenumber, city, 'woonplaats')
        resultBAG = result["response"]["docs"][0]
        item["Woonplaats BAG"] = resultBAG["woonplaatsnaam"]
        item["wkt_latlon"] = resultBAG["centroide_ll"]
        item["wkt_rd"] = resultBAG["centroide_rd"]
        item["Matching"] = 'Alleen woonplaats gevonden, coordinaat is centrum van de stad'
    elif resultBAG.get("huis_nlt"):
        item["Postcode BAG"] = resultBAG["postcode"]
        item["Straatnaam BAG"] = resultBAG["straatnaam"]
        item["Huisnummer BAG"] = resultBAG["huis_nlt"]
        item["Woonplaats BAG"] = resultBAG["woonplaatsnaam"]
        item["wkt_latlon"] = resultBAG["centroide_ll"]
        item["wkt_rd"] = resultBAG["centroide_rd"]
        item["nummeraanduiding_id"] = resultBAG["nummeraanduiding_id"]
        item["Matching"] = 'Match gevonden'
    elif resultBAG.get("straatnaam"):
        item["Straatnaam BAG"] = resultBAG["straatnaam"]
        item["Woonplaats BAG"] = resultBAG["woonplaatsnaam"]
        item["wkt_latlon"] = resultBAG["centroide_ll"]
        item["wkt_rd"] = resultBAG["centroide_rd"]
        item["Matching"] = 'Geen bekend huisnummer, coordinaat is middelpunt van straat'
    if item.get("wkt_latlon") != 'POINT(0 0)':
        xy = re.search(r'(\d+.\d+)\s(\d+.\d+)', item["wkt_latlon"])
        item['lat'] = float(xy.group(1))
        item['lon'] = float(xy.group(2))
        # print("%s" % item['lat'])
        # print("%s" % item['lon'])
    return item


def main():
    requests_cache.install_cache('requests_cache', backend='sqlite', expire_after = 180)
    args = parser().parse_args()
    data = loadSheet(args.filename)
    columns = findColumns(data)
    print('items: ' + str(len(data)))
    first_row = getAddress(data[0], columns)
    with open(args.filename+'_geocoded.csv', 'w') as f:
        w = csv.DictWriter(f, first_row.keys())
        w.writeheader()
        for index, item in enumerate(data):
            print('item: ' + str(index) + ' of ' + str(len(data)))
            item = getAddress(item, columns)
            print(item)
            w.writerow(item)


if __name__ == '__main__':
    main()
