from odoo import models, fields, api
import pandas as pd # type: ignore #check readme for installation on launch.json
from odoo.exceptions import UserError
import base64
from io import BytesIO
from datetime import datetime, timedelta
import pytz
import re

class ArticleEnlistmentWizard(models.TransientModel):
    _name = "article.enlistment.wizard"
    _description = "A wizard form for taking excel sheets of people who want to apply for defense"
    _rec_name = 'term_week_year_course'
    
    # region FIELDS 
    # term_year will be used as the name later for the enlistment object
    term_week_year_course = fields.Char(string='TERM/WEEK/SY')
    excel_file = fields.Binary(string='Imported Excel File')
    failed_record_excel_files = fields.Binary(string='Left Over Records from Excel')
    excel_dataframe_binary = fields.Binary(string='Wizard Enlistment DataFrame')

    excel_column_ids = fields.One2many('article.wizard.excel.column','import_enlistment_wizard_id','Excel Record Column')
    official_record_column_ids = fields.One2many('article.wizard.record.column','import_enlistment_wizard_id','Official Record')

    linked_enlistment_record_ids = fields.Many2many("article.publication","article_enlistment_wizard_successful_relation",string="Existing Enlistment", readonly=True)
    failed_to_search_records_ids = fields.Many2many("article.wizard.publication","article_enlistment_wizard_failed_relation",string="Failed Requests", readonly=True)
    wizard_excel_extracted_record_ids = fields.One2many("article.wizard.publication","import_enlistment_wizard_id","Excel Records", readonly=True)

    enlistment_id = fields.Many2one('article.enlistment','existing_enlistment',compute='_compute_check_for_existing')
    # endregion

    LABEL_TO_RECORD_DICTIONARY = {
                                            'Uploader Email':'uploader_email',
                                            'Uploader Name': 'uploader_name',
                                            'Title': 'name',
                                            'Course Name': 'course_name',
                                            'Adviser': 'adviser',
                                            '1st Author': 'author1',
                                            '2nd Author': 'author2',
                                            '3rd Author': 'author3',
                                            '1st Author Batch Year': 'student_batch_year_1',
                                            '2nd Author Batch Year': 'student_batch_year_2',
                                            '3rd Author Batch Year': 'student_batch_year_3',
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
        #scan the columns
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
        self.excel_dataframe_binary = base64.b64encode(buffer.getvalue())

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
    
    def act_view_enlistment_wizard_page2(self):
        #scan for the row
        enlistment_form_df = self._get_dataframe()
        column_names = enlistment_form_df.columns.tolist()
        # print([column.name for column in self.official_record_column_ids])
        # print([column.name for column in self.excel_column_ids])

        list_of_record_ids = []
        for index, row in enlistment_form_df.iterrows():
            row_record = self._process_row(row)
            list_of_record_ids.append(row_record.id)
        self.wizard_excel_extracted_record_ids = [(6, 0, list_of_record_ids)]
        # print(self.wizard_excel_extracted_record_ids)

        return {
            'type': 'ir.actions.act_window', 
            'name': 'Part 2', 
            'view_mode': 'form', 
            'res_model': 'article.enlistment.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_enlistment_wizard_form_view_part2').id, 'form')], 
            'target': 'current', }

    def act_view_enlistment_wizard_page3(self):
        def _get_course_name():
            user = self.env.user
            if user.has_group('thesis_design_database_manager.group_article_thesis_instructor'):
                return 'thesis'
            elif user.has_group('thesis_design_database_manager.group_article_design_instructor'):
                return 'design'
            else:
                raise UserError('You are not permitted to create enlistments')
        self.ensure_one()
        if not self.enlistment_id:
            course_name = _get_course_name()
            self.enlistment_id = self.env['article.enlistment'].create({'term_week_year_course':self.term_week_year_course+f"_{'T' if course_name == 'thesis' else 'D'}",
                                                                        'course_name':course_name})

        self.failed_to_search_records_ids = [(5, 0, 0)]
        for record in self.wizard_excel_extracted_record_ids:
            if record.error_code == 0:
                # region defense flag
                if record.article_related_id.state in ['draft','proposal_redefense']:
                    final_defense_flag = 0 
                elif record.article_related_id.state in ['pre_final_defense','final_redefense']:
                    final_defense_flag = 1
                else:
                    raise UserError("record went through relation, without error, call admin")
                
                # endregion
                self.enlistment_id.enlisted_article_ids = [(4, record.article_related_id.id, 0)]
                self.linked_enlistment_record_ids = [(4, record.article_related_id.id, 0)]
                record.article_related_id.state = 'final_defense' if final_defense_flag else 'proposal'
            else:
                self.failed_to_search_records_ids = [(4, record.id, 0)]

        return {
            'type': 'ir.actions.act_window', 
            'name': 'Part 3', 
            'view_mode': 'form', 
            'res_model': 'article.enlistment.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_enlistment_wizard_form_view_part3').id, 'form')], 
            'target': 'current', }


    def _get_dataframe(self):
        df_data = base64.b64decode(self.excel_dataframe_binary)
        return pd.read_pickle(BytesIO(df_data)) 
    
    def _process_row(self,row):
        # print("Rows:", row)
        print("processing submission:", row['Name'])
        date_time_completion = self.excel_date_to_odoo_datetime(row['Completion time'])
        if self.env.user.has_group('thesis_design_database_manager.group_article_thesis_instructor'):
            instructor_type = 'T'
        if self.env.user.has_group('thesis_design_database_manager.group_article_design_instructor'):
            instructor_type = 'D'
        
        temp_data_dictionary = {
                                'import_enlistment_wizard_id':self.id,
                                'submission_datetime':date_time_completion,
                                'course':instructor_type,
                            }
        for column in self.excel_column_ids:
            field_name = self.LABEL_TO_RECORD_DICTIONARY[column.official_record_id.name]
            print(field_name,row[column.name])
            temp_data_dictionary[field_name] = row[column.name]

        return self.env['article.wizard.publication'].create(temp_data_dictionary)

    @api.depends('term_week_year_course')
    def _compute_check_for_existing(self):
        for record in self:
            existing_enlistment_id = record.env['article.enlistment'].search([('term_week_year_course', '=', record.term_week_year_course)], limit=1)
            record.enlistment_id = existing_enlistment_id if existing_enlistment_id else None
        return
        

    def excel_date_to_odoo_datetime(self, excel_datetime):
        start_date = datetime(1900, 1, 1)
        if isinstance(excel_datetime, pd.Timestamp):
            excel_datetime = excel_datetime.to_pydatetime()
        delta = excel_datetime - start_date
        odoo_datetime = start_date + delta

        # Convert to UTC and then remove timezone info to make it naive
        local_tz = pytz.timezone('Asia/Manila')  # Replace with your local timezone
        local_datetime = local_tz.localize(odoo_datetime, is_dst=None)
        utc_datetime = local_datetime.astimezone(pytz.utc)
        naive_utc_datetime = utc_datetime.replace(tzinfo=None)

        return naive_utc_datetime.strftime('%Y-%m-%d %H:%M:%S')

    def _get_official_column(self,column_name):
        dictionary_converted_name = self.DEFAULT_EXCEL_COLUMNS_DICTIONARY.get(column_name,False)
        if not dictionary_converted_name: raise UserError("Dictionary Failure, Ask Admin to Fix the dictionary code")
        possible_existing_record_id = self.env['article.wizard.record.column'].search([('name', '=', dictionary_converted_name)],limit=1)
        if possible_existing_record_id: return possible_existing_record_id
        return self.env['article.wizard.record.column'].create({'name': dictionary_converted_name})
