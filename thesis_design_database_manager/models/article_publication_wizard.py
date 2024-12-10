from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import io
import pandas as pd #check readme for installation on launch.json

class ArticleImportExcelWizard(models.TransientModel):
    _name = "article.import.excel.wizard"
    _description = "Import Your Article Excel Files"

    excel_file = fields.Binary(string='Excel File', required=True)
    file_name = fields.Char(string='File Name')

    def import_excel(self):
        if not self.excel_file:
            raise UserError("Please upload an Excel file.")
        
        # Decode the Excel file
        excel_data = base64.b64decode(self.excel_file)
        data_file = io.BytesIO(excel_data)
        
        # Read the Excel file
        article_form_df = pd.read_excel(data_file)
        # print(article_form_df.columns)
        for _, record in article_form_df.iterrows():
            print(record)
        # Process the Excel data
        # for index, row in df.iterrows():
        #     # Example: Assuming the Excel has columns 'name', 'course_name', 'abstract', 'adviser', and 'tags'
        #     name = row['name']
        #     course_name = row['course_name']
        #     abstract = row['abstract']
        #     adviser = row['adviser']
        #     tags = row['tags']
        #     print(name, course_name, abstract, adviser, tags)
