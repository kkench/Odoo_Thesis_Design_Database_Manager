from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import io
import pandas as pd #check readme for installation on launch.json
import datetime

DEFAULT_COLUMN_LINK_DICT = { #EXCEL : OFFICIAL
    "Author 1 (LN, FN MI. ; Alphabetically Arranged)":"1st Author",
    "Author 2 (LN, FN MI.)":"2nd Author",
    "Author 3 (LN, FN MI.)":"3rd Author",
    "Author 1 Student Number":"1st Author Student Number",
    "Author 2 Student Number":"2nd Author Student Number",
    "Author 3 Student Number":"3rd Author Student Number",
    "Topic Title":"Title",
    "Topic Description/Abstract":"Abstract",
    "Topic Tag":"Tags",
    "Main Advisor":"Adviser",
}
"""
Index(['ID', 'Start time', 'Completion time', 'Email', 'Name',
       'Last modified time', 'Author 1 (LN, FN MI. ; Alphabetically Arranged)',
       'Author 1 Student Number', 'Author 2 (LN, FN MI.)',
       'Author 2 Student Number', 'Topic Title', 'Topic Description/Abstract',
       'Topic Tag', 'Main Advisor'],
      dtype='object')
"""

class ArticleImportExcelWizard(models.TransientModel):
    _name = "article.import.excel.wizard"
    _description = "Import Your Article Excel Files"

    excel_file = fields.Binary(string='Excel File', required=True)
    file_name = fields.Char(string='File Name')
    excel_column_ids = fields.One2many('article.wizard.excel.column','import_wizard_id','Excel Record')
    official_record_column_ids = fields.One2many('article.wizard.record.column','import_wizard_id','Official Record')
    wizard_article_form_df = fields.Binary(string='Wizard Article Form DataFrame')
    wizard_new_records_ids = fields.One2many('article.wizard.publications','import_wizard_id','List of New Records')
    wizard_failed_record_ids = fields.One2many('article.wizard.publications','failed_import_wizard_id','List of Failed to Import Records')

    created_article_record_ids = fields.Many2many('article.publication',string="Successful Records")

    user_privilege = fields.Char('User Privilege',compute="_compute_user_privilege")
    COLUMNS_FOR_NEW_ARTICLE_DICT = {
                                            'Title': 'name',
                                            'Course Name': 'course',
                                            'Abstract': 'abstract',
                                            'Adviser': 'adviser',
                                            '1st Author': 'author1',
                                            '2nd Author': 'author2',
                                            '3rd Author': 'author3',
                                            '1st Author Student Number': 'student_number_1',
                                            '2nd Author Student Number': 'student_number_2',
                                            '3rd Author Student Number': 'student_number_3',
                                            'Tags': 'tags',
                                        }
    

    def import_new_articles_excel(self):
        #------------------Setup---------------------
        ms_forms_required_information_list = ['ID','Start time','Completion time','Email','Name','Last modified time']
        new_article_column_list = list(self.COLUMNS_FOR_NEW_ARTICLE_DICT.keys())
        
        if self.user_privilege == "design_instructor":
            new_article_column_list = [col for col in new_article_column_list if col != 'Course Name']
        elif self.user_privilege == "thesis_instructor":
            new_article_column_list = [col for col in new_article_column_list if col not in ['Course Name', '3rd Author','3rd Author Student Number']]
        elif self.user_privilege == "faculty_adviser":
            new_article_column_list = [col for col in new_article_column_list if col != 'Adviser']
        #--------------------------------------------

        #-----------------Error Checks---------------
        if not self.excel_file:
            raise UserError("Please upload an Excel file.")
        if self.user_privilege is None:
            raise UserError("User Has No Authority to Add new Record")
        #--------------------------------------------

        #-----------------Excel Reading--------------
        excel_data = base64.b64decode(self.excel_file)
        data_file = io.BytesIO(excel_data)
        article_form_df = pd.read_excel(data_file)
        

        buffer = io.BytesIO() 
        article_form_df.to_pickle(buffer) 
        self.wizard_article_form_df = base64.b64encode(buffer.getvalue())

        columns = list(article_form_df.columns)
        for data in ms_forms_required_information_list:
            if not data in columns:
                raise UserError("This doesn't seem to be from MS Forms")
        #--------------------------------------------

        #--------Initiate Column Assignment----------
        #Note: This creates new transcient record columns each time, though it may have created multiple 
        #       of the same name record already this will still make it less susceptible to errors if people are uploading at the same time
        #       Furthermore, transcient records will delete itself in due time anyway.
        excel_column_ids_list = []
        for column in columns:
            if column in ms_forms_required_information_list: continue
            record = self.env['article.wizard.excel.column'].create({'name': column})
            excel_column_ids_list.append(record.id)
        self.excel_column_ids = [(6, 0, excel_column_ids_list)]

        official_column_ids_list = []
        for column in new_article_column_list:
            record = self.env['article.wizard.record.column'].create({'name': column})
            official_column_ids_list.append(record.id)
        self.official_record_column_ids = [(6, 0, official_column_ids_list)]
        #------------------------------------------
        
        #-------Get Default Column----------------
        official_column_names = [official_record.name for official_record in self.env['article.wizard.record.column'].browse(official_column_ids_list)]

        for excel_column_id in self.env['article.wizard.excel.column'].browse(excel_column_ids_list):
            official_name = DEFAULT_COLUMN_LINK_DICT.get(excel_column_id.name, None)
            if official_name in official_column_names:
                official_record = self.env['article.wizard.record.column'].search([('name', '=', official_name),('import_wizard_id','=',self.id)])
                if official_record: #not sure if needed since the first line (in this section) finds the colun names already
                    excel_column_id.official_record_id = official_record.id

        #------------------------------

        #----------Go to wizard Page 1-----------------
        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Import CSV', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view').id, 'form')], 
            'target': 'current', }
    
    def act_import_new_article_wizard_part1(self):
        # excel_df = self._get_wizard_df()
        #---------Delete The Temporary Data-----------
        self.wizard_new_records_ids.unlink()
        #---------Return to Page 1
        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Import CSV', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view').id, 'form')], 
            'target': 'current', }

    def act_import_new_article_wizard_part2(self):
        excel_df = self._get_wizard_df()
        new_article_list = []
        for index, row in excel_df.iterrows():
            #---------Static Article Information--------------
            row_data_dictionary = self._get_initial_temp_data(row)
            if self.user_privilege == "design_instructor":
                row_data_dictionary['course'] = 'D'
            elif self.user_privilege == "thesis_instructor":
                row_data_dictionary['course'] = 'T'
            elif self.user_privilege == "faculty_adviser":
                row_data_dictionary['adviser'] = self.env.user.name
            # print(row['Completion time'])
            # row_data_dictionary['registration_date'] = self.excel_date_to_odoo_date(row['Completion time'])
            #-------------------------------------------------

            #----------Excel to Official Column Information-------------
            for excel_column_record in self.excel_column_ids:
                if not excel_column_record.official_record_id:
                    continue
                row_data_dictionary[self.COLUMNS_FOR_NEW_ARTICLE_DICT[excel_column_record.official_record_id.name]] = row[excel_column_record.name]
            new_article = self.env['article.wizard.publications'].create(row_data_dictionary)
            new_article._compute_errors_and_id()
            new_article_list.append(new_article.id)
            #------------------------------------------------------------
        self.wizard_new_records_ids = [(6, 0, new_article_list)]
        #for record in wizard_new_record_ids

        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Part 2', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part2').id, 'form')], 
            'target': 'current', }

    def _get_initial_temp_data(self,row):
        if not self.user_privilege:
            raise UserError("User has no privilege")
        record_dictionary = {
                                'uploader_email':row['Email'],
                                'uploader_name':row['Name'],
                             }
        return record_dictionary

    @api.depends('excel_file')
    def _compute_user_privilege(self):
        for record in self:
            user = self.env.user
            if user.has_group('thesis_design_database_manager.group_article_thesis_instructor'):
                record.user_privilege = "thesis_instructor"
            elif user.has_group('thesis_design_database_manager.group_article_design_instructor'):
                record.user_privilege = "design_instructor"
            elif user.has_group('thesis_design_database_manager.group_article_faculty_adviser'):
                record.user_privilege = "faculty_adviser"
            else:
                record.user_privilege = None

    def excel_date_to_odoo_date(excel_date):
        start_date = datetime.datetime(1900, 1, 1)
        delta = datetime.timedelta(days=int(excel_date) - 2)
        odoo_date = start_date + delta
        return odoo_date.strftime('%Y-%m-%d')

    def _get_wizard_df(self):
        df_data = base64.b64decode(self.wizard_article_form_df)
        return pd.read_pickle(io.BytesIO(df_data))

    def act_upload_new_records(self):
        if not self.wizard_new_records_ids: return #if blank
        failed_record_ids = []
        successfull_records = []
        for form_record in self.wizard_new_records_ids:
            if not form_record.error_code == 0:
                failed_record_ids.append(form_record.id)
                print(form_record.name,"Failed")
                continue
            form_record_advisor = self.env['res.users'].search([('name', '=', form_record.adviser)], limit=1)
            row_record_dictionary = {
                'custom_id':form_record.initial_id,
                'name':form_record.name,
                'state':'proposal',
                'publishing_state':'not_published',
                'course_name':"thesis" if form_record.course == "T" else "design",
                'abstract':form_record.abstract,
                # 'date_registered':form_record.,
                'author1':form_record.author1,
                'author2':form_record.author2,
                'author3':form_record.author3,
                'adviser_ids': [(6, 0, [form_record_advisor.id])],
            }
            print(form_record.name,"Success")
            record = self.env['article.publication'].create(row_record_dictionary)
            successfull_records.append(record.id)
        self.wizard_failed_record_ids = [(6, 0,failed_record_ids)]
        self.created_article_record_ids = [(6, 0,successfull_records)]

        return {
            'type': 'ir.actions.act_window', 
            'name': 'Part 3', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part3').id, 'form')], 
            'target': 'current', }