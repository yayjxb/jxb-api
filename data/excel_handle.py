import openpyxl


class ReadExcel:


    def __init__(self, filename):
        self.workbook = openpyxl.load_workbook(filename)
        self.sheets = self.workbook.get_sheet_names()


    def read_rows(self, sheet):
        """
        获取sheet页的所有数据
        """
        ws = self.workbook[sheet]
        rows = ws.max_row
        cols = ws.max_column
        result = []
        for i in range(1, rows + 1):
            row_list = []
            for j in range(1, cols + 1):
                row_list.append(ws.cell(i, j).value)
            result.append(row_list)
        return result