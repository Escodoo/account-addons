# -*- coding: utf-8 -*-
{
    'name': "Plano de Contas Completo (Brasil)",

    'summary': """
        Plano de Contas Completo Para Empresas Brasileiras""",

    'description': """
        Plano de Contas Completo Para Empresas Brasileiras
    """,

    'author': "ID42 Sistemas",
    'license': 'AGPL-3',
    'website': "https://www.id42.com.br",
    'contributors': [
        'Marcel Savegnago <marcel.savegnago@gmail.com>',
        'João Paulo Carassato <joao.carassato@gmail.com>',
    ],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Localization',
    'version': '12.0.1.0.0',

    'depends': [
       'account'
    ],
    'data': [
        'data/account_chart_template_data.xml',
        'data/account_group.xml',        
        'data/account.account.template.csv',
        'data/account_data.xml',
        'data/account_chart_template_account_account_link.xml',
        'data/account_tax_template_data.xml',
    ],
    'active': True,
}