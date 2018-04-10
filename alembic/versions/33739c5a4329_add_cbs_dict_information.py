#!/usr/bin/python
# -*- coding: utf8 -*-
import os
import pandas as pd
import re, collections

FIELD_NAME = u'שם שדה'
VARIABLE_NAME = u'שם משתנה'
CODE = u'קוד'
SOURCE = u'מקור'
DESCRIPTION = u'מאפיינים'
MILON_SOURCE = u'מילון-טבלה מס'


def get_cbs_variable_name_to_db_name():
    import anyway.field_names
    db_name_to_var_name = {k: v for k, v in vars(anyway.field_names).items() if not k.startswith("__")}
    var_name_to_db_name = {}
    for k, v in db_name_to_var_name.items():
        var_name_to_db_name[v] = k

    return var_name_to_db_name


def read_dict_file(file_path):
    xls = pd.read_csv(file_path, encoding='Windows-1255')
    if 'MS_TAVLA' not in xls.columns and 'MS_TAVLA' in list(xls.iloc[0]):
        xls.columns = xls.iloc[0]
        xls = xls.drop(xls.index[0])

    xls = xls.rename(columns={
        'MS_TAVLA': 'TABLE_NUMBER',
        'KOD': 'CODE',
        'TEUR': 'DESCRIPTION'
    })
    filename = os.path.basename(file_path)
    year = filename[1:5] if filename[0] == 'H' else None
    xls['YEAR'] = year
    xls.DESCRIPTION = xls.DESCRIPTION.astype(unicode).apply(lambda x: x.strip())
    xls = xls[['TABLE_NUMBER', 'CODE', 'DESCRIPTION', 'YEAR']]
    return xls


def get_dictionary_df(dict_files):
    df = pd.DataFrame()
    for f in dict_files:
        new_df = read_dict_file(f)
        df = pd.concat([df, new_df])

    df = df.drop_duplicates()
    return df


def read_excel(excel_path):
    def get_start_index(xls):
        for i in range(0, 10):
            for x in xls.iloc[i]:
                if isinstance(x, collections.Iterable) and x.find(CODE) > -1:
                    return i
        raise Exception('Start index not found')

    xls = pd.read_excel(excel_path)
    xls = xls[get_start_index(xls):].reset_index()
    xls.columns = xls.iloc[0]
    xls = xls.drop(xls.index[0])
    return xls


def read_all_excels(codebook_files):
    df = pd.DataFrame()
    for codebook_file in codebook_files:
        try:
            xls = read_excel(codebook_file)
            xls = xls[[FIELD_NAME, VARIABLE_NAME, CODE, SOURCE, DESCRIPTION]]
            xls.reset_index()
            for i in range(2, len(xls)):
                if pd.isnull(xls.loc[i, VARIABLE_NAME]):
                    xls.loc[i, VARIABLE_NAME] = xls.loc[i - 1, VARIABLE_NAME]
                if pd.isnull(xls.loc[i, FIELD_NAME]):
                    xls.loc[i, FIELD_NAME] = xls.loc[i - 1, FIELD_NAME]

            xls = xls.rename(columns={
                FIELD_NAME: 'FIELD_NAME',
                CODE: 'CODE',
                VARIABLE_NAME: 'VARIABLE_NAME',
                SOURCE: 'SOURCE',
                DESCRIPTION: 'DESCRIPTION'
            })
            codebook_file_name = os.path.basename(codebook_file)
            year = codebook_file_name[1:5] if codebook_file_name[0] == 'H' else None
            xls['YEAR'] = os.path.basename(codebook_files[0])[1:5]
            xls['DESCRIPTION'] = xls['DESCRIPTION'].astype(unicode).apply(lambda x: x.strip())
            df = pd.concat([df, xls])
        except:
            print codebook_file

    return df.drop_duplicates()


def get_cbs_full_dict_data(path):
    codebook_files = []
    dict_files = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            file_path = os.path.join(root, name)
            if file_path.lower().endswith('codebook.xls'):
                codebook_files.append(file_path)
            if file_path.lower().endswith('dictionary.csv'):
                dict_files.append(file_path)

    xls = read_all_excels(codebook_files)
    xls = xls.drop_duplicates()
    xls_with_code = xls[~pd.isnull(xls['CODE'])]
    groups = xls_with_code.groupby(['CODE', 'VARIABLE_NAME']).agg(
        {'DESCRIPTION': max, 'SOURCE': max, 'FIELD_NAME': max})
    xls_with_code = groups.reset_index()
    xls_with_dict = xls[~pd.isnull(xls['SOURCE'])]
    xls_with_dict = xls_with_dict[xls_with_dict['SOURCE'].str.contains(MILON_SOURCE)]
    xls_with_dict['TABLE_NUMBER'] = xls_with_dict['SOURCE'].apply(lambda x: re.findall(r'\d+', x)[0])
    del xls_with_dict['DESCRIPTION']
    del xls_with_dict['CODE']

    dict_df = get_dictionary_df(dict_files)

    xls_with_dict_merged = pd.merge(xls_with_dict, dict_df)
    xls = pd.concat([xls_with_dict_merged, xls_with_code])
    xls = xls[~pd.isnull(xls['CODE'])]

    cbs_var_name_to_db_name = get_cbs_variable_name_to_db_name()
    xls['DB_NAME'] = xls.apply(lambda x: cbs_var_name_to_db_name.get(x['VARIABLE_NAME']), axis=1)

    return xls


"""Add cbs dict information

Revision ID: 33739c5a4329
Revises: 3c0d35fdbe2e
Create Date: 2018-04-09 18:47:06.951936

"""

# revision identifiers, used by Alembic.
revision = '33739c5a4329'
down_revision = '3c0d35fdbe2e'
branch_labels = None
depends_on = None

from alembic import op

TABLE_NAME = 'cbs_dictionary'
VIEW_NAME = 'cbs_dict_view'


def upgrade():
    df = get_cbs_full_dict_data('./static/data/cbs/')
    renamed_column = {}
    for col in df.columns:
        renamed_column[col] = col.lower()
    df = df.rename(columns=renamed_column)
    df.to_sql(TABLE_NAME, op.get_bind())
    op.get_bind().execute(
        """
            create or replace view %s as 
            select variable_name, db_name, code, max(description) as description
            from %s 
            group by variable_name, db_name, code
        """ % (VIEW_NAME, TABLE_NAME)
    )


def downgrade():
    op.get_bind().execute('drop view %s;' % VIEW_NAME)
    op.drop_table(TABLE_NAME)
