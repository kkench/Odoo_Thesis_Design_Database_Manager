from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import io
import pandas as pd # type: ignore #check readme for installation on launch.json
import datetime


class ArticleImportExcelWizard(models.TransientModel):
    _name = "article.import.excel.wizard"
    _description = "Import Your Article Excel Files"

    excel_file = fields.Binary(string='Excel File', required=True)
    file_name = fields.Char(string='File Name')
    excel_column_ids = fields.One2many('article.wizard.excel.column','import_wizard_id','Excel Record')
    official_record_column_ids = fields.One2many('article.wizard.record.column','import_wizard_id','Official Record')
    wizard_article_form_df = fields.Binary(string='Wizard Article Form DataFrame')
    wizard_type = fields.Selection([
                                        ("null", "None Set"),
                                        ("new", "New Articles"),
                                        ("edit", "Edit Articles"),
                                    ],"Type of Wizard",default="null")
    wizard_excel_extracted_record_ids = fields.One2many("article.wizard.publication","import_wizard_id","Excel Records")
    created_article_record_ids = fields.Many2many('article.publication', 'article_import_excel_wizard_created_rel',string="Successful Records")
    updated_article_records_ids = fields.Many2many('article.publication', 'article_import_excel_wizard_updated_rel',string="Updated Records")
    overwritten_article_record_ids = fields.Many2many('article.publication', 'article_import_excel_wizard_overwritten_rel',string="Overwritten Records")
    failed_form_submissions_record_ids = fields.Many2many("article.wizard.publication", 'article_import_excel_wizard_failed_rel',string="Failed Records")
    # duplicate_extracted_author_submission_ids = fields.Many2many("article.wizard.publication", 'article_import_excel_wizard_duplicate_rel',string="Duplicate Submission")

    popup_message = fields.Char("Warning", readonly=True)
    user_privilege = fields.Char('User Privilege',compute="_compute_user_privilege")

    DEFAULT_COLUMN_LINK_DICT_FOR_NEW_MODE = { #EXCEL : OFFICIAL
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
        "Main Adviser":"Adviser",
    }

    DEFAULT_COLUMN_LINK_DICT_FOR_EDITING_MODE = {
        #DEFAULT FIELDS FOR FINDING CORRECT RECORD
        "Author 1 (LN, FN MI. ; Alphabetically Arranged)":"1st Author",
        "Author 2 (LN, FN MI.)":"2nd Author",
        "Author 3 (LN, FN MI.)":"3rd Author",
        "Author 1 Student Number":"1st Author Student Number",
        "Author 2 Student Number":"2nd Author Student Number",
        "Author 3 Student Number":"3rd Author Student Number",
        "Main Advisor":"Adviser",
        "Main Adviser":"Adviser",
        #QUESTIONS FOR THINGS TO UPDATE
        "Is this update a Topic Change/Redefense?":"For Redefense?",
        "Will You Update Title?":"For Title Update?",
        "Will You Update the Abstract/Description?":"For Abstract Update?",
        "Will you update the tags?":"For Tag Update?",
        #RELATED FIELDS FOR RECORDS
        "Updated Title Name":"Title",
        "Updated Abstract":"Abstract",
        "Updated Tags (Include Former Tags)":"Tags",
        "New Title Name":"Title",
        "New Abstract":"Abstract",
        "New Topic Tags":"Tags",
    }

    LABEL_TO_RECORD_DICTIONARY = {
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
    
    #NEW RECORDS
    def act_set_import_new(self):
        self.wizard_type = "new"
        return self.import_excel_articles()

    def process_new_data_for_part_2(self):
        excel_df = self._get_wizard_df()
        new_article_list = []
        for index, row in excel_df.iterrows():
            #---------Static Article Information--------------
            row_data_dictionary = self._get_initial_temp_data(row)
            #-------------------------------------------------

            #----------Excel to Official Column Information-------------
            for excel_column_record in self.excel_column_ids:
                if not excel_column_record.official_record_id:
                    continue    
                row_data_dictionary[self.LABEL_TO_RECORD_DICTIONARY[excel_column_record.official_record_id.name]] = row[excel_column_record.name]
            new_article = self.env['article.wizard.publication'].create(row_data_dictionary)
            # new_article._compute_data_and_errors()
            new_article_list.append(new_article.id)
            #------------------------------------------------------------
        #--------------Set all record relation-------------
        self.wizard_excel_extracted_record_ids = [(6, 0, new_article_list)]

        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Part 2', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part2').id, 'form')], 
            'target': 'current', }

    def act_upload_temporary_record(self):
        if self.wizard_type == 'new':
            return self.upload_process_for_new_record()
        elif self.wizard_type == 'edit':
            return self.upload_process_for_edit_record()

    def upload_process_for_new_record(self):
        records_with_related_authors = self.wizard_excel_extracted_record_ids.mapped('article_to_update_id')
        if not records_with_related_authors: return self.upload_new_records_to_database()

        authors_to_rewrite = ""
        for related_records in records_with_related_authors:
            authors_to_rewrite += f", {related_records.custom_id.split('_')[0]}" if authors_to_rewrite != "" else related_records.custom_id.split('_')[0]
        
        self.popup_message = "Related authors' paper status will reset and will be overwritten: " + authors_to_rewrite

        return {
            'name': 'Upload Confirmation',
            'type': 'ir.actions.act_window',
            'res_model': 'article.import.excel.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('thesis_design_database_manager.article_final_warning_confirmation_popup_form').id,
            'target': 'new',
        }

    def upload_process_for_edit_record(self):
        for temp_record in self.wizard_excel_extracted_record_ids:
            authors_to_reset_status = ""
            if temp_record.error_code: continue
            if int(temp_record.edit_binary_string[0]) == 1:
                authors_to_reset_status += f", {temp_record.initial_id.split('_')[0]}" if authors_to_reset_status != "" else temp_record.initial_id.split('_')[0]

            if authors_to_reset_status == "": return self.upload_edit_records_to_database()

            self.popup_message = "Related authors' paper status will reset their status to proposal redefense: " + authors_to_reset_status

        return {
            'name': 'Upload Confirmation',
            'type': 'ir.actions.act_window',
            'res_model': 'article.import.excel.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('thesis_design_database_manager.article_final_warning_confirmation_popup_form').id,
            'target': 'new',
        }


    def act_upload_records(self):
        if self.wizard_type == "new":
            return self.upload_new_records_to_database()
        elif self.wizard_type == "edit":
            return self.upload_edit_records_to_database()

    def upload_new_records_to_database(self):
        if not self.wizard_excel_extracted_record_ids or self.wizard_type == "null":
            return  # if blank
        record_created_list = []
        record_overwritten_list = []
        record_failed_list = []
        record_updated_list = []
        for form_record in self.wizard_excel_extracted_record_ids:
            if form_record.error_code != 0:
                record_failed_list.append(form_record.id)
                continue
            form_record_advisor = self.env['res.users'].search([('name', '=', form_record.adviser)], limit=1)
            row_record_dictionary = {
                'custom_id': form_record.initial_id,
                'name': form_record.name,
                'state': 'proposal',
                'publishing_state': 'not_published',
                'course_name': "thesis" if form_record.course == "T" else "design",
                'abstract': form_record.abstract,
                'author1': form_record.author1,
                'author2': form_record.author2,
                'author3': form_record.author3,
                'adviser_ids': [(6, 0, [form_record_advisor.id])],
            }
            if not form_record.article_to_update_id:
                record = self.env['article.publication'].create(row_record_dictionary)
                record_created_list.append(record.id)
            else:
                record = form_record.article_to_update_id.write(row_record_dictionary)
                record_overwritten_list.append(form_record.article_to_update_id.id)
            
        self.created_article_record_ids = [(6, 0, record_created_list)]
        self.overwritten_article_record_ids = [(6, 0, record_overwritten_list)]
        self.failed_form_submissions_record_ids = [(6, 0, record_failed_list)]
        self.updated_article_records_ids = [(6, 0, record_updated_list)]

        return {
            'type': 'ir.actions.act_window', 
            'name': 'Part 3', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part3').id, 'form')], 
            'target': 'current', }

    def upload_edit_records_to_database(self):
        record_overwritten_list = []
        record_failed_list = []
        record_updated_list = []

        for temp_record in self.wizard_excel_extracted_record_ids:
            record_dictionary = {'custom_id': temp_record.initial_id,}
            override_everything = int(temp_record.edit_binary_string[0])
            update_title_flag = int(temp_record.edit_binary_string[1])
            update_abstract_flag = int(temp_record.edit_binary_string[2])
            update_tag_flag = int(temp_record.edit_binary_string[3])
            if temp_record.error_code:
                record_failed_list.append(temp_record.id)
                continue
            if update_title_flag or override_everything:
                record_dictionary['name'] = temp_record.name
            if update_abstract_flag or override_everything:
                record_dictionary['abstract'] = temp_record.abstract
            if update_tag_flag or override_everything:
                pass #input tag update here
            if override_everything:
                record_dictionary['state'] = 'proposal'
                record_dictionary['publishing_state'] = 'not_published'
            temp_record.article_to_update_id.write(record_dictionary)
            if override_everything:
                record_overwritten_list.append(temp_record.article_to_update_id.id)
            else:
                record_updated_list.append(temp_record.article_to_update_id.id)

        self.overwritten_article_record_ids = [(6, 0, record_overwritten_list)]
        self.failed_form_submissions_record_ids = [(6, 0, record_failed_list)]
        self.updated_article_records_ids = [(6, 0, record_updated_list)]

        return {
            'type': 'ir.actions.act_window', 
            'name': 'Part 3', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part3').id, 'form')], 
            'target': 'current', }
    #EXISTING RECORDS
    def act_edit_existing_articles(self):
        self.wizard_type = "edit"
        return self.import_excel_articles() 
    
    def process_edit_data_for_part_2(self):
        boolean_dictionary = {
            "No (both conformity and non conformity purposes)":0,
            "Yes (New topic/redefense for a new topic)":1,
            "No":"0",
            "Yes":"1",
        }
        excel_df = self._get_wizard_df()
        to_update_article_list = []
        to_update_questions_list = ["For Redefense?","For Title Update?","For Abstract Update?","For Tag Update?"]
        update_data = ["Updated Title Name","Updated Abstract","Updated Tags (Include Former Tags)"]
        new_record_data = ["New Title Name","New Abstract","New Topic Tags"]
        question_columns = [excel_column_record for excel_column_record in self.excel_column_ids 
                            if excel_column_record.official_record_id.name in to_update_questions_list]
        non_question_columns = [excel_column_record for excel_column_record in self.excel_column_ids 
                                    if (excel_column_record.official_record_id.name not in to_update_questions_list) 
                                    and excel_column_record.official_record_id]
        for _, row in excel_df.iterrows():
            #---------Static Article Information--------------
            row_data_dictionary = self._get_initial_temp_data(row)
            boolean_string_flags = list("0000")
            #-------------------------------------------------
            #------------Extract Questions To Update-----------
            for column in question_columns:
                boolean_index = to_update_questions_list.index(column.official_record_id.name)
                boolean_string_flags[boolean_index] = str(boolean_dictionary.get(row[column.name], "0"))
            boolean_string_flags = "".join(boolean_string_flags)
            # print(boolean_string_flags)
            row_data_dictionary['edit_binary_string'] = boolean_string_flags
            #------------Update/New Data ----------
            not_important_header_list = update_data if int(boolean_string_flags[0]) else new_record_data
            # print("testing:",not_important_header_list)
            appropriate_non_question_columns = [column for column in non_question_columns 
                                                if column.name not in not_important_header_list]
            
            for column in appropriate_non_question_columns:
                row_data_dictionary[self.LABEL_TO_RECORD_DICTIONARY[column.official_record_id.name]] = row[column.name]

            if not int(boolean_string_flags[0]):
                row_data_dictionary['name'] = row_data_dictionary.get('name',None) if boolean_string_flags[1] else None
                row_data_dictionary['abstract'] = row_data_dictionary.get('abstract',None) if boolean_string_flags[2] else None
                row_data_dictionary['tags'] = row_data_dictionary.get('tags',None)if boolean_string_flags[3] else None
            print(row_data_dictionary)
            temporary_record = self.env['article.wizard.publication'].create(row_data_dictionary)
            # temporary_record._compute_data_and_errors()

            to_update_article_list.append(temporary_record.id)
        #--------------Set all record relation-------------
        self.wizard_excel_extracted_record_ids = [(6, 0, to_update_article_list)]

        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Part 2', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part2').id, 'form')], 
            'target': 'current', }

    #Reusable Functions
    def import_excel_articles(self):
        if self.wizard_type == "null":return
        #------------------Setup---------------------
        ms_forms_required_information_list = ['ID','Start time','Completion time','Email','Name','Last modified time']
        columns_needed = self.get_new_column_list()
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

        #--------Initiate Column Assignment (This is Default Values)---------- 
        #Note: This creates new transcient record columns each time, though it may have created multiple 
        #       of the same name record already this will still make it less susceptible to errors if people are uploading at the same time
        #       Furthermore, transcient records will delete itself in due time anyway.
        excel_column_ids_list = []
        # print(columns)
        for column in columns:
            if column in ms_forms_required_information_list:
                continue  # Removes the MS headers
            record = self.env['article.wizard.excel.column'].create({'name': column})
            excel_column_ids_list.append(record.id)
        self.excel_column_ids = [(6, 0, excel_column_ids_list)]

        official_column_ids_list = []
        name_check = []
        for column in columns_needed:
            possible_existing_record_id = self.env['article.wizard.record.column'].search([('name', '=', column)])
            if not possible_existing_record_id:
                record = self.env['article.wizard.record.column'].create({'name': column})
            else: 
                record = possible_existing_record_id
            official_column_ids_list.append(record.id)
            name_check.append(record.name)
        # print(name_check)
        self.official_record_column_ids = [(6, 0, official_column_ids_list)]
        #------------------------------------------
        
        #-------Get Default Column----------------
        official_column_names = [official_record.name for official_record in self.env['article.wizard.record.column'].browse(official_column_ids_list)]

        for excel_column_id in self.env['article.wizard.excel.column'].browse(excel_column_ids_list):
            official_name = (self.DEFAULT_COLUMN_LINK_DICT_FOR_NEW_MODE.get(excel_column_id.name, None) 
                             if self.wizard_type == "new" else
                             self.DEFAULT_COLUMN_LINK_DICT_FOR_EDITING_MODE.get(excel_column_id.name, None))
            if official_name in official_column_names:
                official_record = self.env['article.wizard.record.column'].search([('name', '=', official_name),('import_wizard_id','=',self.id)])
                if official_record: #not sure if needed since the first line (in this section) finds the colun names already
                    excel_column_id.official_record_id = official_record.id
        #------------------------------
        #-------------------------------
        #----------Go to wizard Page 1-----------------
        return { 
                        'type': 'ir.actions.act_window', 
                        'name': 'Import CSV', 
                        'view_mode': 'form', 
                        'res_model': 'article.import.excel.wizard',
                        'res_id': self.id,
                        'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view').id, 'form')], 
                        'target': 'current', }

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

    def act_import_return_article_wizard_part1(self):
        if self.wizard_type == "null":return
        # excel_df = self._get_wizard_df()
        #---------Delete The Temporary Data-----------
        self.wizard_excel_extracted_record_ids.unlink()
        #---------Return to Page 1
        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Import CSV', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view').id, 'form')], 
            'target': 'current', }
    
    def act_import_article_wizard_part2(self):
        if self.wizard_type == "null":return
        if self.wizard_type == "new":
            return self.process_new_data_for_part_2()
        if self.wizard_type == "edit":
            return self.process_edit_data_for_part_2()

    def get_new_column_list(self):
        if self.wizard_type == "new":
            new_article_column_list = list(self.DEFAULT_COLUMN_LINK_DICT_FOR_NEW_MODE.values()) 
        elif self.wizard_type == "edit":                             
            new_article_column_list = list(self.DEFAULT_COLUMN_LINK_DICT_FOR_EDITING_MODE.values()) 
        if self.user_privilege == "design_instructor":
            new_article_column_list = [col for col in new_article_column_list if col != 'Course Name']
        elif self.user_privilege == "thesis_instructor":
            new_article_column_list = [col for col in new_article_column_list if col not in ['Course Name', '3rd Author','3rd Author Student Number']]
        elif self.user_privilege == "faculty_adviser":
            new_article_column_list = [col for col in new_article_column_list if col != 'Adviser']
        return new_article_column_list

    def excel_date_to_odoo_date(excel_date):
        start_date = datetime.datetime(1900, 1, 1)
        delta = datetime.timedelta(days=int(excel_date) - 2)
        odoo_date = start_date + delta
        return odoo_date.strftime('%Y-%m-%d')

    def _get_wizard_df(self):
        df_data = base64.b64decode(self.wizard_article_form_df)
        return pd.read_pickle(io.BytesIO(df_data)) 
    
    def _get_initial_temp_data(self,row):
        if not self.user_privilege:
            raise UserError("User has no privilege")
        record_dictionary = {
                                'uploader_email':row['Email'],
                                'uploader_name':row['Name'],
                                'import_wizard_id':self.id,
                            }
        
        if self.user_privilege == "design_instructor":
                record_dictionary['course'] = 'D'#############FIX THIS LATER
        elif self.user_privilege == "thesis_instructor":
            record_dictionary['course'] = 'T'
        elif self.user_privilege == "faculty_adviser":
            record_dictionary['adviser'] = self.env.user.name
        return record_dictionary