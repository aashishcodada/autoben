import pandas as pd
import numpy as np
from lxml import html as lh
from lxml.cssselect import CSSSelector
from pypdf import PdfWriter

class PDFGenerator:
    def __init__(self, filepath, porfpath):
        self.PATH_TO_HTML = filepath
        self.PATH_TO_PORF = porfpath

        self.DT_TODAY = pd.to_datetime('today')
        self.COLFIELDS = ['DescriptionRow', 'ItemRow', 'Extended PriceRow', 'QtyRow', 'Unit PriceRow']
        self.ROWFIELDS = ['A', 'B', 'C', 'D'] + np.r_[1:31].astype(str).tolist()

        df_list = pd.read_html(self.PATH_TO_HTML, match="USD", flavor='bs4')
        cols = df_list[-2].rename(columns={df_list[-2].columns[0]:'Supplier Name'})
        items = df_list[-1]
        items.columns = cols.columns
        self.items = (
            items
            .iloc[:-2]
            .drop(columns="Details")
            .assign(Price=lambda x: x.Price.str.replace(r'[^0-9.]', '', regex=True).astype(float))
            .assign(Quantity= lambda x: x.Quantity.astype(int))
            .fillna('')
        )

        tree = lh.parse(self.PATH_TO_HTML).getroot()
        sel = CSSSelector("h1.x1f")
        self.REQNO = sel(tree)[0].text_content().strip().split()[-1]

    def make_pdf(self, name, grp):
        writer = PdfWriter(self.PATH_TO_PORF)
        group = grp.reset_index(drop=True)
        grid = np.meshgrid(self.COLFIELDS, self.ROWFIELDS[:len(group)], indexing='ij')
        fields = np.char.add(grid[0], grid[1]).T.astype(object)

        fd = {
            'Vendor Name': name,
            'Req#': self.REQNO,
            'Date1_af_date': self.DT_TODAY.strftime('%m/%d/%Y'),
            'Extended PriceGrand Total': f"{group['Amount  (USD)'].sum():.2f}",
            'PAGE 2_Total': f"{group['Amount  (USD)'].iloc[4:].sum():.2f}"
        }
        form_data = group.iloc[:, 1:].values
        fd.update(dict(zip(fields.flatten(), form_data.flatten())))

        for page in writer.pages:
            writer.update_page_form_field_values(page, fd, auto_regenerate=True)

        writer.write(f"{self.DT_TODAY.strftime('%Y%m%d')} {name.replace('/', "").replace("\\", "")}.pdf")

        return fd
