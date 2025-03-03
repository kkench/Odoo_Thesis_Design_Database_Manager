from odoo import api,fields,models
from difflib import get_close_matches
import re

class ArticleWizardPublication(models.TransientModel):
    _name = "article.wizard.publication"
    _description = "Sample list of what will be uploaded"

    name = fields.Char("Title")
    course = fields.Selection([("T", "T"),("D", "D")],string="Course Code")
    initial_id = fields.Char("ID",compute="_compute_data_and_errors",readonly=True,store=True)
    uploader_email = fields.Char("Uploader Email", readonly=True)
    uploader_name = fields.Char("Uploader Name", readonly=True)
    abstract = fields.Text("Abstract")
    author1 = fields.Char("Author1", default=None)
    author2 = fields.Char("Author2", default=None)
    author3 = fields.Char("Author3", default=None)
    adviser = fields.Char("ADVISER")
    student_batch_year_1 = fields.Char("Student 1 Batch Year", default=None)
    student_batch_year_2 = fields.Char("Student 2 Batch Year", default=None)
    student_batch_year_3 = fields.Char("Student 3 Batch Year", default=None)
    
    article_2_flag = fields.Boolean("Check if Article 2",default=False)
    article_related_id = fields.Many2one("article.publication","If Author has already existing ID",compute="_compute_data_and_errors",store=True)
    edit_binary_string = fields.Char("Editing Binary",default="0000")# Binary Boolean String; (1-If Complete Redefense; 2-Title Update; 3-Abstract Update; 4-Tag Update) 

    tags = fields.Text("TAGS")
    error_code = fields.Integer("Error Code Number", compute="_compute_data_and_errors", readonly=True, store=True)
    error_comment = fields.Char("Comments", compute="_compute_data_and_errors", readonly=True, store=True)

    import_article_wizard_id = fields.Many2one("article.import.excel.wizard", default=None)
    checking_wizard_id = fields.Many2one("article.import.excel.wizard")
    to_create_tag_ids = fields.Many2many("article.wizard.publication.tag", "article_wizard_pub_new_tags")
    similar_tag_ids = fields.Many2many("article.wizard.publication.tag", "article_wizard_pub_similar_tags")
    existing_tag_ids = fields.Many2many("article.wizard.publication.tag", "article_wizard_pub_existing_tags")
    duplicate_temp_to_create_ids = fields.Many2many("article.wizard.publication.tag", "article_wizard_pub_duplicate_temps")

    import_enlistment_wizard_id = fields.Many2one("article.enlistment.wizard", default=None)

    submission_datetime = fields.Datetime("Time of Submission", readonly=True)
    
    def reset_record(record):
        record.initial_id = None

    @api.depends('author1', 'author2', 'author3', 'uploader_email', 'tags','course', 'student_batch_year_1', 'student_batch_year_2', 'student_batch_year_3', 'adviser','import_article_wizard_id')
    def _compute_data_and_errors(self):
        ''' Error Codes:
        0 - No Errors
        1 - Incorrect Name Format (Cannot Read) 
        2 - Student is not the editor
        3 - Invalid Course
        4 - Student Number Does Not Follow Proper Formatting
        5 - 3rd Author Exists on Thesis
        6 - Duplicate Submission
        7 - Tags Stuff
        8 - Cannot Search Adviser
        9+ - Enlistment Error
        '''
        for record in self:
            record.error_comment = ""
            if not record.is_author_name_valid():
                record.error_code = 1
                record.error_comment = "One of the Author is not proper name format!"
                record.reset_record()
                continue             
            if not record.does_author_email_and_name_match(): 
                record.error_code = 2
                record.error_comment = "Uploader Error; Use Own Mapuan Email"
                record.reset_record()
                continue
            if record.course_is_unknown(): 
                record.error_code = 3
                record.error_comment = "No Course Given"
                record.reset_record()
                continue
            if not record.is_student_batch_year_in_format():
                record.error_code = 4
                record.error_comment = "Student Number not Correct Format"
                record.reset_record()
                continue
            record.arrange_authors_alphabetically()
            record._update_initial_id()
            # print(record.initial_id)
            if record.course == "D" and (None in [record.author1,record.author2,record.author3]): # only max 2 authors for thesis
                record.error_code = 5
                record.error_comment = "2 Authors only for Thesis"
                record.reset_record()
                continue
            if record.record_has_duplicate_submission():
                #the if function already processes the record if there is duplicate submission
                continue
            record._check_for_existing_records()


            #wizard_specific_checks
            if record.import_article_wizard_id:
                if record.import_article_wizard_id.wizard_type == "new":
                    if record._has_errors_for_new_articles(): #check if anything is wrong for new record
                        record.reset_record()
                        continue
                    if record.article_related_id:
                        record.error_comment = "Existing Title Exists, Will Overwrite"
                elif record.import_article_wizard_id.wizard_type == "edit":
                    if record._has_errors_for_edit_articles():
                        record.reset_record()
                        continue
                    record.link_existing_record_for_editing()
                record.error_code = 0
                record._process_tags()
                record.clear_newline_from_abstract_and_title()
            elif record.import_enlistment_wizard_id:
                record._process_enlistment()
            else:
                record.error_code = 999
                record.error_comment = "no wizard attached"

        return

    ###FOR ERROR CHECKING (_compute_data_and_errors())
    def _process_enlistment(record):
        record.error_code = 0
        record.error_comment = "pass"
        if not record.article_related_id:
            record.error_code = 9
            record.error_comment = "Existing Study Cannot Be Found in Database"
            return
        if not (record.article_related_id.state == 'draft'
                or record.article_related_id.state == 'proposal_redefense'
                or record.article_related_id.state == 'pre_final_defense'
                or record.article_related_id.state == 'final_redefense'):
            record.error_code = 10
            record.error_comment = "Existing Study is Not Ready For Defense"
        return

    def is_author_name_valid(self):
        #THIS IS A COMPUTE FUNCTION, DONT EDIT NON STORED RECORD DATA
        pattern_name = r'^[A-Z][a-z]+, ([A-Z][a-z]+ )+[A-Z]\.$'  # LN, FN MI
        if not (self.author1 or self.author2 or self.author3): return False
        for author_name in [self.author1, self.author2, self.author3]:
            if not author_name: continue
            if not re.match(pattern_name, author_name):
                return False
        return True

    def record_has_duplicate_submission(self):
        # Search for existing records with the same name and initial_id
        # print(self.initial_id)
        existing_temporary_data_ids = self.env['article.wizard.publication'].search([
            ('initial_id', '=', self.initial_id),
            ('id', '!=', self.id if isinstance(self.id, int) else None),  # Exclude the current record   
            ('import_article_wizard_id', '=', self.import_article_wizard_id.id),
        ])
        # print("The IDs are")
        # print(existing_temporary_data_ids)
        if not existing_temporary_data_ids: return False
        if not self.submission_datetime: return True
        for existing_temporary_data_id in existing_temporary_data_ids:
            if existing_temporary_data_id.error_code != 0 or not existing_temporary_data_id.submission_datetime: continue
            if existing_temporary_data_id.submission_datetime > self.submission_datetime: #previous duplicate record is later
                self.error_code = 6
                self.error_comment = "Another Submission has been Made"
                self.reset_record()
                return True
            existing_temporary_data_id.error_code = 6
            existing_temporary_data_id.error_comment = "Another Submission has been Made"
            existing_temporary_data_id.reset_record()
        return False

    def does_author_email_and_name_match(self):
        #THIS IS A COMPUTE FUNCTION, DONT EDIT NON STORED DATA
        pattern_mymail = r'^[a-zA-Z0-9._%+-]+@mymail\.mapua\.edu\.ph$'
        if not re.match(pattern_mymail, self.uploader_email):
            return False
        for author_name in [self.author1, self.author2, self.author3]:
            email_check = self.create_email_from_format(author_name) == self.uploader_email
            name_check = self.create_name_from_format_of_author(author_name) == self.uploader_name
            if email_check and name_check:
                return True
        return False #did not match any

    def create_email_from_format(self,name):
        if not isinstance(name, str): return "error"
        last_name, first_name_middle_initial = name.split(', ')
        first_names, middle_initial = first_name_middle_initial.rsplit(' ', 1)
        email = f"{''.join([name[0].lower() for name in first_names.split()])}{middle_initial[0].lower()}{last_name.lower()}@mymail.mapua.edu.ph"
        return email
    
    def create_name_from_format_of_author(self,name):
        if not isinstance(name, str): return "error"
        upper_name = name.upper()
        last_name, first_name_middle_initial = upper_name.split(', ')
        first_names, _ = first_name_middle_initial.rsplit(' ', 1)
        return first_names + " " + last_name
        
    def adviser_is_searchable(self):
        # THIS IS A COMPUTE FUNCTION, DONT EDIT NON STORED DATA
        if not self.adviser:
            return False

        for adviser_name in self.adviser.split(';'):
            adviser = self.env['res.users'].search([('name', '=', adviser_name)], limit=1)
            print(adviser)

            if adviser:
                if adviser.has_group('thesis_design_database_manager.group_article_faculty_adviser'):
                    continue  # Continue checking the next adviser if the group matches
                else:
                    return False  # Return False if the adviser does not have the required group
            else:
                return False  # Found an adviser that is not searcheable

        return True  # Return True if all advisers have the required group

    def is_student_batch_year_in_format(self):
        # THIS IS A COMPUTE FUNCTION, DON'T EDIT NON-STORED DATA    
        student_list = [self.author1, self.author2, self.author3]
        student_batch_years = [self.student_batch_year_1, self.student_batch_year_2, self.student_batch_year_3]
        pattern = r'20\d{2}'
        #term_pattern = r'([1-3]T\d{4})|([1-4]Q\d{4})''
        
        for student,student_number in zip(student_list,student_batch_years):
            if student_number and not re.match(pattern, student_number):
                return False
            if student and not student_number:
                return False
        
        return not all(student_number is None for student_number in student_batch_years)

    def course_is_unknown(self):
        return not (self.course in ['T','D'])

    def _has_errors_for_new_articles(self):
        #the function that calls this will cycle the records already, keep it as 'self' 
        #THIS IS A COMPUTE FUNCTION, DONT EDIT NON STORED DATA
        print("for new records")
        if not self.adviser_is_searchable():
            print("adviser is not searchable")
            self.error_code = 8
            self.error_comment = "Adviser is Not Found"
            return True
        if self.record_has_the_same_title_as_existing():
                self.error_code = 10
                self.error_comment = "Title Already Exists on Database"
                return True
        return False
    
    def record_has_the_same_title_as_existing(self):
        if self.env['article.publication'].search([('name', '=', self.name)], limit=1):
            return True
        return False

    def _has_errors_for_edit_articles(self):
        #self is already a single instance
        #this assumes wizard is on edit mode
        if not self.article_related_id:
            self.error_code = 9
            self.error_comment = "Cannot Find Existing Record"
            self.article_related_id = None
            return True
        
        is_proper_instructor = ((self.import_article_wizard_id.user_privilege == 'thesis_instructor' and self.course == 'T') or
            (self.import_article_wizard_id.user_privilege == 'design_instructor' and self.course == 'D'))

        if is_proper_instructor:
            return False
            
        self.error_code = 10
        self.error_comment = "User is not an instructor"
        return True

    def _check_for_existing_records(self):
        if not self.initial_id: return False
        existing_record_article = self.env['article.publication'].search([('custom_id', '=', self.initial_id)], limit=1)
        if existing_record_article: #not an error but will allocate updates to the old data
            self.article_related_id = existing_record_article.id
            return True
        else:
            self.article_related_id = None
            return False
    ##########################

    def _update_initial_id(self):
        for record in self:
            #--------------GET THE LAST NAMES IN ORDER----------------------
            record.initial_id = record.author1.split(', ')[0] #last name
            record.initial_id += record.author2.split(', ')[0] if record.author2 else ""
            record.initial_id += record.author3.split(', ')[0] if record.author3 else ""
            #-------------Get latest student Batch Number----------------
            latest_batch_number =  max([int(batch_year) for batch_year in [record.student_batch_year_1,record.student_batch_year_2,record.student_batch_year_3] if not 0])
            record.initial_id += "_" + str(latest_batch_number)
            #-------------Include Course Initial------------------
            record.initial_id += "_" + record.course
            #-------------For Thesis Articles-----------------------
            if record.course == "T":
                record.initial_id += "_Art2" if record.article_2_flag else "_Art1"
            print(record.initial_id)
            return

    def arrange_authors_alphabetically(self):
        author_student_number = {
            self.author1: self.student_batch_year_1,
            self.author2: self.student_batch_year_2,
            self.author3: self.student_batch_year_3,
        }
        author_names = [name for name in [self.author1, self.author2, self.author3] if name]
        
        # Sort the names alphabetically
        sorted_names = sorted(author_names)
        # Fill with None to ensure the list has 3 elements
        sorted_names.extend([None] * (3 - len(sorted_names)))
        sorted_student_number = [author_student_number[author_name] if author_name else None for author_name in sorted_names]
        if sorted_names == [self.author1, self.author2, self.author3]:
            return True
        else:
            self.author1, self.author2, self.author3 = sorted_names
            self.student_batch_year_1, self.student_batch_year_2, self.student_batch_year_3 = sorted_student_number
            return False

    def clear_newline_from_abstract_and_title(self):
        for record in self:
            if not record.abstract: continue
            abstract = record.abstract 
            abstract = re.sub(r'\n+', ' ', abstract)
            abstract = re.sub(r'\s{2,}', ' ', abstract)
            record.abstract = abstract
            
            title = record.name
            title = re.sub(r'\n+', ' ', title)
            title = re.sub(r'\s{2,}', ' ', title)
            record.name = title
            
    def _process_tags(self):
        if not self.tags:
            invalid_tags = []
        else:
            article_tags = self.excel_tags_to_odoo_tags(self.tags)
            invalid_tags = self.get_tag_changes(article_tags)
        return
    
    def act_open_error_code(self):
        self.ensure_one()
        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Error', 
            'view_mode': 'form', 
            'res_model': 'article.wizard.publication',
            'res_id': self.id,
            'views': [(self.env.ref('thesis_design_database_manager.view_article_wizard_publication_error_code_popup').id, 'form')], 
            'target': 'new', }
    
    def act_open_existing_record(self):
        self.ensure_one()
        if not self.article_related_id:
            return
        return { 
            'type': 'ir.actions.act_window', 
            'name': 'Form', 
            'view_mode': 'form', 
            'res_model': 'article.publication',
            'res_id': self.article_related_id.id,
            'views': [(self.env.ref('thesis_design_database_manager.article_publication_form_view').id, 'form')], 
            'target': 'new', }
    
    def link_existing_record_for_editing(self):
        # print("another one bites the dust")
        binary_string = self.edit_binary_string
        # print(binary_string)
        if binary_string == "0000" or not binary_string:
            return False
        if not self.article_related_id:
            return False
        if int(binary_string[0]):  # Edit everything
            return True
        else:
            # print(bool(int(binary_string[1])),bool(int(binary_string[2])),bool(int(binary_string[3])))
            # self.adviser = self.article_related_id.adviser_ids
            semicolon_separated_advisers = "" 
            for adviser_id in self.article_related_id.adviser_ids:
                semicolon_separated_advisers += adviser_id.name if semicolon_separated_advisers == "" else f";{adviser_id.name}"
            self.adviser = semicolon_separated_advisers
            if not int(binary_string[1]):  # If not supposed to edit, copy it
                # print("title checked")
                self.name = self.article_related_id.name
            if not int(binary_string[2]):
                # print("abstract checked")
                self.abstract = self.article_related_id.abstract
            if int(binary_string[3]):
                pass  
        return True

    ################# ADDITIONAL FROM EXTENSION

    @staticmethod
    def excel_tags_to_odoo_tags(tag_string):
        provided_tags = []
        provided_tags = tag_string.split(';')
        return provided_tags  

    @staticmethod
    def check_abbreviation(keywords):
        abbreviations = []
        for tag in keywords:
            if (tag.isupper() and (len(tag) > 1)):
               abbreviations.append(tag)
        return abbreviations
         #([A-Z\S]{2,}+) [A-Z] is all uppercase \S ignore all whitespace {2,}
        #regex for later to make abbreviation checking work better if no correction via menu is implemented
    
    def check_similar_tags(self, keywords):  
            
        similar_tags = []
        tags_to_create = []
        existing_tags = []
        duplicate_temps = []
        all_tags = self.env['article.tag'].search([])
        tag_names = [tag.name for tag in all_tags]
        for tag in keywords:
            found_tag = get_close_matches(tag, tag_names)
            duplicate = self.env["article.wizard.publication.tag"].search([('name', '=', tag)],limit=1)
            if found_tag == "" or tag == "":
                    continue
            if duplicate and not found_tag: #first redundancy check
                    duplicate_temps.append(duplicate.id)
            elif not found_tag:
                    created_tag = self.env["article.wizard.publication.tag"].create({ 'name': tag })
                    tags_to_create.append(created_tag.id)
                    # print(created_tag.name)
            elif tag in found_tag:
                    existing_tag = self.env["article.wizard.publication.tag"].create({ 'name': tag })
                    existing_tags.append(existing_tag.id)
            else:
                    sim_tag = self.env["article.wizard.publication.tag"].create({ 'name': tag })
                    similar_tags.append(sim_tag.id)
            self.to_create_tag_ids = [(6,0,tags_to_create)]
            self.similar_tag_ids = [(6,0,similar_tags)]
            self.existing_tag_ids = [(6,0,existing_tags)]
            self.duplicate_temp_to_create_ids = [(6,0,duplicate_temps)]
            # print(similar_tags)
        return similar_tags or existing_tags or tags_to_create
    
    
    def get_tag_changes(self, tag_list):
        sim = self.check_similar_tags(tag_list)
        if (not sim and not self.to_create_tag_ids.exists()):
            needs_change = False
        else:
            needs_change = True
        return needs_change
    
class ArticleWizardTempTags(models.TransientModel):
    _name = "article.wizard.publication.tag"

    name = fields.Char("Tag Name")
    article_wizard_publication_ids = fields.Many2many("article.wizard.publication")
