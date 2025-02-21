from odoo import models, fields, api
import pandas as pd # type: ignore #check readme for installation on launch.json
from odoo.exceptions import UserError
import base64
from io import BytesIO

class ArticleEnlistmentWizard(models.TransientModel):
    _name = "article.enlistment.wizard"
    _description = "A wizard form for taking excel sheets of people who want to apply for defense"
    _rec_name = 'term_year_batch'
    
    # region FIELDS 
    # term_year_batch will be used as the name later for the enlistment object
    term_year_batch = fields.Char(string='TERM/YEAR/BATCH')
    excel_file = fields.Binary(string='Imported Excel File')
    failed_record_excel_files = fields.Binary(string='Left Over Records from Excel')
    linked_enlistment_record_id = fields.Many2one(string="Existing Enlistment")
    excel_dataframe = fields.Binary(string='Wizard Enlistment DataFrame')

    excel_column_ids = fields.One2many('article.wizard.excel.column','import_enlistment_wizard_id','Excel Record Column')
    official_record_column_ids = fields.One2many('article.wizard.record.column','import_enlistment_wizard_id','Official Record')
    # endregion

    LABEL_TO_RECORD_DICTIONARY = {
                                            'Email':'uploader_email',
                                            'Uploader Name': 'uploader_name',
                                            'Title': 'name',
                                            'Course Name': 'course_name',
                                            'Adviser': 'adviser',
                                            '1st Author': 'author1',
                                            '2nd Author': 'author2',
                                            '3rd Author': 'author3',
                                            '1st Author Batch Year': 'batch_number_1',
                                            '2nd Author Batch Year': 'batch_number_2',
                                            '3rd Author Batch Year': 'batch_number_3',
                                        }
    
    DEFAULT_EXCEL_COLUMNS_DICTIONARY = {
        #DEFAULT FIELDS FOR FINDING CORRECT RECORD
        'Email': 'Uploader Email',
        'Name': 'Uploader Name',
        "Title":"Title",
        'Course Name': 'Course Name',
        "Author 1":"1st Author",
        "Author 2":"2nd Author",
        "Author 3":"3rd Author",
        "Author 1 Batch Year":"1st Author Batch Year",
        "Author 2 Batch Year":"2nd Author Batch Year",
        "Author 3 Batch Year":"3rd Author Batch Year",
        "Main Advisor":"Adviser",
        "Main Adviser":"Adviser",
    }
    
    def act_view_enlistment_wizard_page1(self):
        FORMS_COLUMN_CHECK_LIST = ['ID','Start time','Completion time','Email','Name','Last modified time']
        FORMS_COLUMN_TO_REMOVE = [column for column in FORMS_COLUMN_CHECK_LIST if column not in ['Email','Name']]
        if not self.excel_file: 
            raise UserError("Please upload an Excel file.")

        try:
            excel_data = base64.b64decode(self.excel_file)
            data_file = BytesIO(excel_data)
            enlistment_form_df = pd.read_excel(data_file)
        except:
            raise UserError("File is not an excel file")
    
        buffer = BytesIO() 
        enlistment_form_df.to_pickle(buffer) 
        self.excel_dataframe = base64.b64encode(buffer.getvalue())

        excel_column_list = list(enlistment_form_df.columns)
        for checking_column in FORMS_COLUMN_CHECK_LIST:
            if checking_column.lower() == 'id': #ID randomizes in capital, idk why might look into normalization
                continue
            if checking_column not in excel_column_list:
                raise UserError("File is not an MS Forms Excel")

        self.excel_column_ids = [(5, 0, 0)]
        self.official_record_column_ids = [(5, 0, 0)]
        for column in excel_column_list:
            if (column in FORMS_COLUMN_TO_REMOVE) or (column.lower == 'id'):
                continue
            
            record_excel_column = self.env['article.wizard.excel.column'].create({'name': column})
            self.excel_column_ids = [(4, record_excel_column.id, 0)]
            ###this may not be efficient, but considering this is only the columns, speed should not matter
            for expected_column in tuple(self.DEFAULT_EXCEL_COLUMNS_DICTIONARY.keys()):
                if expected_column.lower() in record_excel_column.name.lower():
                    if ('batch' in record_excel_column.name.lower()) and  ('batch' not in expected_column.lower()):
                        continue # need to have batch year on both expected and column name
                    official_record_column = self._get_official_column(expected_column)
                    self.official_record_column_ids = [(4, official_record_column.id, 0)]
                    record_excel_column.official_record_id = official_record_column
                    break
        return {
            'type': 'ir.actions.act_window', 
            'name': 'Part 1', 
            'view_mode': 'form', 
            'res_model': 'article.enlistment.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_enlistment_wizard_form_view_part1').id, 'form')], 
            'target': 'current', }
    
    def _get_dataframe(self):
        pass
        # if not self.excel_file:
        #     raise UserError("Please upload an Excel file.")
        # return

    def _get_official_column(self,column_name):
        possible_existing_record_id = self.env['article.wizard.record.column'].search([('name', '=', column_name)],limit=1)
        if possible_existing_record_id: return possible_existing_record_id
        return self.env['article.wizard.record.column'].create({'name': column_name})
