from bag_geocode import loadSheet
import xlwt


def write_row(worksheet, row=0, column=0, labels=''):
    ws = worksheet
    for label in labels:
        ws.write(row, column, label=label)
        column += 1
    return ws


def create_test_excel(tmpdir, rows):
    wb = xlwt.Workbook()
    ws = wb.add_sheet('testsheet')
    row_number = 0
    for row in rows:
        write_row(ws, row_number, 0, rows)
        row_number += 1
    filename = '{}'.format(tmpdir.join("test.xls"))
    wb.save(filename)
    return filename


def test_loadSheet_returns_list_when_title_row(tmpdir, header=True):
    rows = [['title', 'adres', 'huisnummer', 'postcode', 'stad'],
            ['Match', 'Postjeskade', '8-H', '1057DR', 'Amsterdam']]
    filename = create_test_excel(tmpdir, rows)
    loaded_sheet = loadSheet(filename, header=header)
    assert isinstance(loaded_sheet, list)
    assert len(loaded_sheet) == 1


def test_loadSheet_returns_empty_list_when_no_header_row(tmpdir, header=False):
    no_header_row = [['Match', 'Postjeskade', '8-H', '1057DR', 'Amsterdam']]
    filename = create_test_excel(tmpdir, no_header_row)
    loaded_sheet = loadSheet(filename)
    assert isinstance(loaded_sheet, list)
    assert len(loaded_sheet) == 0
