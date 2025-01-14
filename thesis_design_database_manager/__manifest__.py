{
    "name": "Thesis/Design Database Manager",
    "description": """A comprehensive database manager for thesis and design projects. 
                    This module helps in updating the status of studies, managing student 
                    groups, and identifying studies with similar parameters. It includes 
                    features for secure access control, user-friendly views, and efficient 
                    data management.""",
    "category": "Database Manager",
    "depends": [
        "base",
        "web",
    ],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/article_publication_views.xml",
        "views/article_tag_views.xml",
        "views/article_advisor_view.xml",
        "views/wizard_views/debugging_views/for_debugging_only_view.xml",
        "views/wizard_views/article_import_article_popup_view.xml",
        "views/wizard_views/article_import_form.xml",
        "views/article_menus.xml",
    ],
    "assets": { 'web.assets_backend': 
               [ 'thesis_design_database_manager/static/src/css/custom_styles.css', 
                ], 
    },
    "application": True,
    "license": "LGPL-3"
}