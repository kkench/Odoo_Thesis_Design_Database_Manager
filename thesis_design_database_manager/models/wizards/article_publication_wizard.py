from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
from io import BytesIO
import pandas as pd # type: ignore #check readme for installation on launch.json
# from difflib import SequenceMatcher, get_close_matches
from datetime import datetime, timedelta
import pytz


class ArticleImportExcelWizard(models.TransientModel):
    _name = "article.import.excel.wizard"
    _description = "Import Your Article Excel Files"

    excel_file = fields.Binary(string='Excel File', required=True)
    file_name = fields.Char(string='File Name')
    excel_column_ids = fields.One2many('article.wizard.excel.column','import_article_wizard_id','Excel Record')
    official_record_column_ids = fields.One2many('article.wizard.record.column','import_article_wizard_id','Official Record')
    wizard_article_form_df = fields.Binary(string='Wizard Article Form DataFrame')
    wizard_type = fields.Selection([
                                        ("null", "None Set"),
                                        ("new", "New Articles"),
                                        ("edit", "Edit Articles"),
                                    ],"Type of Wizard",default="null")
    wizard_excel_extracted_record_ids = fields.One2many("article.wizard.publication","import_article_wizard_id","Excel Records")
    created_article_record_ids = fields.Many2many('article.publication', 'article_import_excel_wizard_created_rel',string="Successful Records")
    updated_article_records_ids = fields.Many2many('article.publication', 'article_import_excel_wizard_updated_rel',string="Updated Records")
    voided_article_record_ids = fields.Many2many('article.publication', 'article_import_excel_wizard_voided_rel',string="Voided Records")
    failed_form_submissions_record_ids = fields.Many2many("article.wizard.publication", 'article_import_excel_wizard_failed_rel',string="Failed Records")
    wizard_check_tags_records_ids = fields.One2many('article.wizard.publication','checking_wizard_id','List of Records for Checking')

    ignore_instructor_privilege = fields.Boolean("As Adviser, not Instructor", default=False)

    popup_message = fields.Char("Warning", readonly=True)
    user_privilege = fields.Selection([
                                            ('thesis_instructor', 'Thesis Instructor'),
                                            ('design_instructor', 'Design Instructor'),
                                            ('faculty_adviser', 'Faculty Adviser')
                                        ], string='User Privilege', compute='_compute_user_privilege', store=True)


    DEFAULT_COLUMN_LINK_DICT = { #EXCEL : OFFICIAL
        "Author 1":"1st Author",
        "Author 2":"2nd Author",
        "Author 3":"3rd Author",
        "Author 1 Batch Year":"1st Author Batch Year",
        "Author 2 Batch Year":"2nd Author Batch Year",
        "Author 3 Batch Year":"3rd Author Batch Year",
        "Title":"Title",
        "Abstract":"Abstract",
        "Description":"Abstract",
        "Tag":"Tags",
        "Advisor":"Adviser",
        "Adviser":"Adviser",
        "Article 2?":"Article 2 Flag",
        'Email': 'Uploader Email',
        'Name': 'Uploader Name',
    }

    QUESTIONS_FOR_EDIT_MODE = {
        #QUESTIONS FOR THINGS TO UPDATE
        "Topic Change?":"For Redefense?",
        "Redefense?":"For Redefense?",
        "Change Topic?":"For Redefense?",
        "Title?":"For Title Update?",
        "Description?":"For Abstract Update?",
        "Abstract?":"For Abstract Update?",
        "Tags?":"For Tag Update?",
        "Article 2?":"Article 2 Flag",
    }

    LABEL_TO_RECORD_DICTIONARY = {
                                            'Title': 'name',
                                            'Course Name': 'course',
                                            'Abstract': 'abstract',
                                            'Adviser': 'adviser',
                                            '1st Author': 'author1',
                                            '2nd Author': 'author2',
                                            '3rd Author': 'author3',
                                            '1st Author Batch Year': 'student_batch_year_1',
                                            '2nd Author Batch Year': 'student_batch_year_2',
                                            '3rd Author Batch Year': 'student_batch_year_3',
                                            'Tags': 'tags',
                                            'Article 2 Flag':'article_2_flag',
                                            'Uploader Email': 'uploader_email',
                                            'Uploader Name': 'uploader_name',
                                        }
    #Buttons
    def act_set_import_new(self):
        self.wizard_type = "new"
        return self.import_excel_articles_part1()
    
    def act_set_import_new_and_as_adviser(self):
        self.ignore_instructor_privilege = True
        return self.act_set_import_new()

    def act_edit_existing_articles(self):#This now only takes care of instructors as only the people allowed to edit
        # self.ignore_instructor_privilege = True
        self.wizard_type = "edit"
        return self.import_excel_articles_part1() 

    def act_upload_records(self):
        if self.wizard_type == "new":
            return self.upload_new_records_to_database()
        elif self.wizard_type == "edit":
            return self.upload_edit_records_to_database()

    def act_upload_temporary_record(self):
        if self.wizard_type == 'new':
            return self.upload_process_for_new_record()
        elif self.wizard_type == 'edit':
            return self.upload_process_for_edit_record()

    def act_import_article_wizard_part2(self):
        if self.wizard_type == "null":return
        if self.wizard_type == "new":
            return self.process_new_data_for_part_2()
        if self.wizard_type == "edit":
            return self.process_edit_data_for_part_2()


    #GENERAL PROCESSES
    def import_excel_articles_part1(self):
        if self.wizard_type == "null":return
        FORMS_COLUMN_CHECK_LIST = ['ID','Start time','Completion time','Email','Name']
        FORMS_COLUMN_TO_REMOVE = [column for column in FORMS_COLUMN_CHECK_LIST if column not in ['Email','Name']]
        if not self.excel_file:
            raise UserError("Please upload an Excel file.")
        if self.user_privilege is None:
            raise UserError("User Has No Authority to Add new Record")

        # region Excel Reading
        try:
            excel_data = base64.b64decode(self.excel_file)
            data_file = BytesIO(excel_data)
            article_form_df = pd.read_excel(data_file)
        except:
            raise UserError("File is not an excel file")
    
        buffer = BytesIO() 
        article_form_df.to_pickle(buffer) 
        self.wizard_article_form_df = base64.b64encode(buffer.getvalue())

        # print(article_form_df.head())
        excel_column_list = list(article_form_df.columns)
        for check_column in FORMS_COLUMN_CHECK_LIST:
            if check_column.lower() not in [item.lower() for item in excel_column_list]:
                raise UserError("File is not an MS Forms Excel")

        self.excel_column_ids = [(5, 0, 0)]
        self.official_record_column_ids = [(5, 0, 0)]
        for column in excel_column_list:
            # print(f"{column.lower()} in {[item.lower() for item in FORMS_COLUMN_TO_REMOVE]}:{column.lower() in [item.lower() for item in FORMS_COLUMN_TO_REMOVE]}")
            if column.lower() in [item.lower() for item in FORMS_COLUMN_TO_REMOVE]:
                continue
            record_excel_column = self.env['article.wizard.excel.column'].create({'name': column})
            self.excel_column_ids = [(4, record_excel_column.id, 0)]
            for expected_column in tuple(self.DEFAULT_COLUMN_LINK_DICT.keys()):
                if expected_column.lower() in record_excel_column.name.lower():
                    if ('batch' in record_excel_column.name.lower()) and  ('batch' not in expected_column.lower()):
                        continue # need to have batch year on both expected and column name
                    if ('?' in record_excel_column.name.lower()) and  ('?' not in expected_column.lower()): #might cause article
                        continue
                    if ('title' in record_excel_column.name.lower()) and  ('title' not in expected_column.lower()): 
                        continue
                    # print(expected_column.lower())
                    official_record_column = self._get_official_column(expected_column,self.DEFAULT_COLUMN_LINK_DICT)
                    self.official_record_column_ids = [(4, official_record_column.id, 0)]
                    record_excel_column.official_record_id = official_record_column
                    continue

            if self.wizard_type == 'edit':
                for expected_column in tuple(self.QUESTIONS_FOR_EDIT_MODE.keys()) :
                    if expected_column.lower() in record_excel_column.name.lower():
                        # print(expected_column.lower())
                        official_record_column = self._get_official_column(expected_column,self.QUESTIONS_FOR_EDIT_MODE)
                        self.official_record_column_ids = [(4, official_record_column.id, 0)]
                        record_excel_column.official_record_id = official_record_column
                        continue


        #----------Go to wizard Page 1-----------------
        return { 
                        'type': 'ir.actions.act_window', 
                        'name': 'Import CSV', 
                        'view_mode': 'form', 
                        'res_model': 'article.import.excel.wizard',
                        'res_id': self.id,
                        'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view').id, 'form')], 
                        'target': 'current', }


    def process_new_data_for_part_2(self):
        excel_df = self._get_wizard_df()
        new_article_list = []
        instructor_type = 'T' if self.user_privilege == 'thesis_instructor' else 'D'
        for _, row in excel_df.iterrows():
            date_time_completion = self.excel_date_to_odoo_datetime(row['Completion time'])
            row_data_dictionary = {
                'import_article_wizard_id':self.id,
                'submission_datetime':date_time_completion,
                'course':instructor_type,
            }
            for column in self.excel_column_ids:
                if not column.official_record_id: continue                 
                field_name = self.LABEL_TO_RECORD_DICTIONARY[column.official_record_id.name]
                if field_name == 'article_2_flag': 
                    row_data_dictionary[field_name] = 1 if 'yes' in row[column.name].lower() else 0#self.boolean_dictionary.get(row[column.name],False)
                    continue
                row_data_dictionary[field_name] = row[column.name]

            new_article = self.env['article.wizard.publication'].create(row_data_dictionary)
            new_article_list.append(new_article.id)
            
            self.wizard_excel_extracted_record_ids = [(6, 0, new_article_list)]

        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Part 2', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part2').id, 'form')], 
            'target': 'current', }

    def process_edit_data_for_part_2(self):
        excel_df = self._get_wizard_df()
        instructor_type = 'T' if self.user_privilege == 'thesis_instructor' else 'D'
        question_list = ["For Redefense?","For Title Update?","For Abstract Update?","For Tag Update?"]
        
        to_update_article_list = []
        # print(excel_df.head())
        for _, row in excel_df.iterrows():
            date_time_completion = self.excel_date_to_odoo_datetime(row['Completion time'])
            row_data_dictionary = {
                'import_article_wizard_id':self.id,
                'submission_datetime':date_time_completion,
                'course':instructor_type,
            }
            binary_string = list('0000')
            print(f"ROW: :{row['Id']}")
            for column in self.excel_column_ids:
                if not column.official_record_id: 
                    continue
                
                excel_column_name = column.name
                data = row[excel_column_name]
                official_column_name = column.official_record_id.name

                if pd.isna(data):
                    continue
            
                if official_column_name in question_list:
                    index_in_string = question_list.index(official_column_name)
                    input_column_value = '1' if 'yes' in data.lower() else '0'
                    binary_string[index_in_string] = input_column_value
                    continue

                field_name = self.LABEL_TO_RECORD_DICTIONARY[official_column_name]
                if field_name == 'article_2_flag':
                    row_data_dictionary[field_name] = 1 if 'yes' in data.lower() else 0
                    continue
                
                if 'batch' in field_name: #need to be str, not integer; for regex and later id
                    data = str(int(data))#remove float decimals
                    
                row_data_dictionary[field_name] = data
            row_data_dictionary['edit_binary_string'] = ''.join(binary_string)
            temporary_record = self.env['article.wizard.publication'].create(row_data_dictionary)
            to_update_article_list.append(temporary_record.id)

            self.wizard_excel_extracted_record_ids = [(6, 0, to_update_article_list)]
        
        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Part 2', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_part2').id, 'form')], 
            'target': 'current', }

    def upload_process_for_new_record(self):
        records_with_related_authors = self.wizard_excel_extracted_record_ids.mapped('article_related_id')
        if not records_with_related_authors: return self.upload_new_records_to_database()

        authors_to_rewrite = ""
        for related_records in records_with_related_authors:
            authors_to_rewrite += f", {related_records.custom_id.split('_')[0]}" if authors_to_rewrite != "" else related_records.custom_id.split('_')[0]
        
        self.popup_message = "Related authors' paper status will have to re-propose  and previous studies will be voided: " + authors_to_rewrite

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

    def upload_new_records_to_database(self):
        if not self.wizard_excel_extracted_record_ids or self.wizard_type == "null":
            return  # if blank
        record_created_list = []
        record_voided_list = []
        record_failed_list = []
        record_updated_list = []
        for form_record in self.wizard_excel_extracted_record_ids:
            all_tags = []
            tag_list = self.set_similar_tags(form_record)
            all_tags.extend(tag_list)
            if form_record.error_code != 0:
                record_failed_list.append(form_record.id)
                continue
            else:
                new_tag_obj = self.set_new_tags(form_record)
                all_tags.extend(new_tag_obj)
            form_record_advisor = self.env['res.users'].search([('name', '=', form_record.adviser)], limit=1)
            row_record_dictionary = {
                'custom_id': form_record.initial_id,
                'name': form_record.name,
                'course_name': "thesis" if form_record.course == "T" else "design",
                'state': "draft" if not form_record.article_2_flag else "article_2_approval_request",
                'abstract': form_record.abstract,
                'author1': form_record.author1,
                'author2': form_record.author2,
                'author3': form_record.author3,
                'article2_flag': form_record.article_2_flag,
                'adviser_ids': [(6, 0, [form_record_advisor.id])], # this is new, so replace is good
                'article_tag_ids': [(6, 0, [tag.id for tag in all_tags])],
            }
            if not form_record.article_related_id:
                record = self.env['article.publication'].create(row_record_dictionary)
                record_created_list.append(record.id)
            else:
                form_record.article_related_id.act_void_topic()
                record = self.env['article.publication'].create(row_record_dictionary)
                record_voided_list.append(form_record.article_related_id.id)
                record_created_list.append(record.id)
            
        self.created_article_record_ids = [(6, 0, record_created_list)]
        self.voided_article_record_ids = [(6, 0, record_voided_list)]
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
        record_voided_list = []
        record_failed_list = []
        record_updated_list = []

        for temp_record in self.wizard_excel_extracted_record_ids:
            record_dictionary = {'custom_id': temp_record.initial_id,}
            override_everything = int(temp_record.edit_binary_string[0])
            update_title_flag = int(temp_record.edit_binary_string[1])
            update_abstract_flag = int(temp_record.edit_binary_string[2])
            update_tag_flag = int(temp_record.edit_binary_string[3])

            all_tags = []
            tag_list = self.set_similar_tags(temp_record)
            all_tags.extend(tag_list)
            new_tag_obj = self.set_new_tags(temp_record)
            all_tags.extend(new_tag_obj)
            
            if temp_record.error_code:
                record_failed_list.append(temp_record.id)
                continue
            if update_title_flag or override_everything:
                record_dictionary['name'] = temp_record.name
            if update_abstract_flag or override_everything:
                record_dictionary['abstract'] = temp_record.abstract
            if update_tag_flag or override_everything:
                record_dictionary['article_tag_ids'] = [(6, 0, [tag.id for tag in all_tags])] #input tag update here
                #currently untested
            if override_everything:
                record_dictionary['state'] = 'draft'
                record_dictionary['publishing_state'] = 'not_published'
            temp_record.article_related_id.write(record_dictionary)
            if override_everything:
                record_voided_list.append(temp_record.article_related_id.id)
            else:
                record_updated_list.append(temp_record.article_related_id.id)

        self.voided_article_record_ids = [(6, 0, record_voided_list)]
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

    #Reusable Functions
    def _get_official_column(self,column_name,dictionary):
        # print(column_name)
        dictionary_converted_name = dictionary.get(column_name,False)
        if not dictionary_converted_name: raise UserError("Dictionary Failure, Ask Admin to Fix the dictionary code")
        possible_existing_record_id = self.env['article.wizard.record.column'].search([('name', '=', dictionary_converted_name)],limit=1)
        if possible_existing_record_id: return possible_existing_record_id
        return self.env['article.wizard.record.column'].create({'name': dictionary_converted_name})

    @api.depends('excel_file','ignore_instructor_privilege')
    def _compute_user_privilege(self):
        for record in self:
            user = self.env.user
            if user.has_group('thesis_design_database_manager.group_article_thesis_instructor') and not self.ignore_instructor_privilege:
                record.user_privilege = "thesis_instructor"
            elif user.has_group('thesis_design_database_manager.group_article_design_instructor') and not self.ignore_instructor_privilege:
                record.user_privilege = "design_instructor"
            # elif user.has_group('thesis_design_database_manager.group_article_faculty_adviser') or self.ignore_instructor_privilege:
            #     record.user_privilege = "faculty_adviser"
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

    def _get_wizard_df(self):
        df_data = base64.b64decode(self.wizard_article_form_df)
        return pd.read_pickle(BytesIO(df_data)) 
    
    def unlink(self):
        #######################
        for record in self:
            #excel is custom per wizard
            #official is reused so no need to unlink
            #created,updated,and overwritten are official records already,dont unlink
            #failed came from wizard_excel_extracted_record_ids, so it deletes itself
            for excel_column in record.excel_column_ids:
                excel_column.unlink()
            for excel_extracted_record in record.wizard_excel_extracted_record_ids:
                excel_extracted_record.unlink()
        #####################
        result = super(ArticleImportExcelWizard, self).unlink()
        return result
    
    ##### ADDED FROM EXTENSION #########
    def act_go_to_view_tags(self):
        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Part 2-2', 
            'view_mode': 'form', 
            'res_model': 'article.import.excel.wizard',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_import_excel_wizard_form_view_tags').id, 'form')], 
            'target': 'current', }
    
    def set_similar_tags(self, temp_record):       
        similar_tag_names = [tag.name for tag in temp_record.similar_tag_ids]
        similar_tag_names.extend([tag.name for tag in temp_record.existing_tag_ids])
        similar_tag = self.env["article.tag"].search([('name','in', similar_tag_names)])
       
        return similar_tag
    
    def set_new_tags(self, temp_record):
        tag_list = []
        new_tag_names = [ntag.name for ntag in temp_record.to_create_tag_ids]
        for n_tag in new_tag_names:
            tag_dict = {"name": n_tag}
            tag_list.append(tag_dict)
        new_tag = self.env["article.tag"].create(tag_list)
        return new_tag