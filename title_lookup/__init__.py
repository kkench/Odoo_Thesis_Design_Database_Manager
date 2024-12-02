# -*- coding: utf-8 -*-
# More info at https://www.odoo.com/documentation/master/reference/module.html

{
    "name": "Thesis/Design Database Manager",
    "depends": [
        "base",
        "web",
    ],
    "data": [
        "security\ir.model.access.csv",
        "views\article_info_views.xml",
        "views\article_menus.xml"
        # "views\estate_property_views.xml",
        # "views\estate_menus.xml",
        # "views\estate_property_offer_views.xml",
        # "views\estate_property_type_views.xml",
        # "views\estate_property_tag_views.xml",
        # "views/res_users_views.xml",
    ],
    "application": True,
    "license": "LGPL-3",
}