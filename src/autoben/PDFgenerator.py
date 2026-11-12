import numpy as np
import pandas as pd
from lxml import html as lh
from lxml.cssselect import CSSSelector
from pypdf import PdfWriter


class PDFGenerator:
    def __init__(self, filepath, porfpath):
        self.PATH_TO_HTML = filepath
        self.PATH_TO_PORF = porfpath

        self.PERSON = 'AASHISH'
        self.DT_TODAY = pd.to_datetime('today')
        self.COLFIELDS = ['DescriptionRow', 'ItemRow', 'Extended PriceRow', 'QtyRow', 'Unit PriceRow']
        self.ROWFIELDS = ['A', 'B', 'C', 'D'] + np.r_[1:31].astype(str).tolist()

        df_list = pd.read_html(self.PATH_TO_HTML, attrs={'id':'LinesTableRN:Content'})
        cols = df_list[-1]
        cols = cols.rename(columns={cols.columns[0]:'Supplier Name'})
        items = df_list[-1]
        items.columns = cols.columns
        self.items = (
            items
            [['Supplier Name', 'Description', 'Supplier Item Number', 'Amount (USD)', 'Quantity', 'Price']]
            .iloc[:-1]
        )
        self.items['Quantity'] = self.items['Quantity'].astype('Int64').fillna(1)
        self.items["Price"] = (
            self.items["Price"]
            .str.replace(r"[^0-9.]", "", regex=True)
            .astype("Float64")
            .combine_first(self.items["Amount (USD)"])
        )

        tree = lh.parse(self.PATH_TO_HTML).getroot()
        sel = CSSSelector("h1.x1f")
        self.REQNO = sel(tree)[0].text_content().strip().split()[-1]

    def save_pdf(self, name, grp):
        writer = PdfWriter(self.PATH_TO_PORF)
        group = grp.reset_index(drop=True)
        grid = np.meshgrid(self.COLFIELDS, self.ROWFIELDS[:len(group)], indexing='ij')
        fields = np.char.add(grid[0], grid[1]).T.astype(object)

        fd = {
            'Vendor Name': name,
            'Req#': self.REQNO,
            'Date1_af_date': self.DT_TODAY.strftime('%m/%d/%Y'),
            'Extended PriceGrand Total': f"{group['Amount (USD)'].sum():.2f}",
            'PAGE 2_Total': f"{group['Amount (USD)'].iloc[4:].sum():.2f}"
        }
        form_data = group.iloc[:, 1:].astype(str).fillna('').values
        fd.update(dict(zip(fields.flatten(), form_data.flatten())))

        for page in writer.pages:
            writer.update_page_form_field_values(page, fd, auto_regenerate=True)

        writer.write(f"{self.DT_TODAY.strftime('%Y%m%d')} {name.replace('/', "").replace("\\", "")}.pdf")

        return fd

    def save_excel(self):
        items = self.items.copy()
        items['_blank'] = ''
        items['Date'] = self.DT_TODAY.strftime('%m/%d/%Y')
        items['BenBuys'] = 'Y'
        items['ReqNo'] = self.REQNO
        items['Person'] = self.PERSON

        items = items.astype(str).fillna('')

        items = items[['Date', '_blank', 'Supplier Name', 'Description', 'BenBuys',
            'Supplier Item Number', 'Price', 'Quantity', 'Amount (USD)',
            '_blank', 'ReqNo', '_blank', 'Person']]

        items.to_excel(f"{self.DT_TODAY.strftime('%Y%m%d')}.xlsx", index=False)
