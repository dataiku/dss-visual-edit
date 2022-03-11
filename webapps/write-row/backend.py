import dataiku
import pandas as pd
from flask import request
from dataiku.core.sql import SQLExecutor2
from dataiku.customwebapp import *

# Access parameters that end-users filled in using webapp config
DATASET_NAME = get_webapp_config()['input_dataset']

# Initialize the SQL executor
ds = dataiku.Dataset(DATASET_NAME)
table_name = ds.get_config()['params']['table'] # nom de la table correspondant à ce dataset
connection_name = ds.get_config()['params']['connection'] # nom de la connexion SQL dataiku où aller récupérer la table
executor = SQLExecutor2(connection=connection_name)

client = dataiku.api_client()
project = client.get_default_project()
import dataikuapi
dscreator = dataikuapi.dss.dataset.DSSManagedDatasetCreationHelper(project, DATASET_NAME + "_changes")
if (not dscreator.already_exists()):
    dscreator.with_store_into(connection="filesystem_managed")
    dscreator.create()

@app.route('/get_dataset_schema')
def get_dataset_schema():
    """
        Ici on récupère le schema de la table et on 
        exécute une requête SQL sur la table source et on renvoie un objet type dictionnaire pour paramétrer le formulaire :
        [
            {
                "name" : "nom_de_colonne",
                "type" : "categorical",
                "uniques" : ["val_1","val_2"],
                "child" : "child_column", # si la valeur de ce champ conditionne la valeur d'un autre champ, il a un élément child 
                "parent" : "parent_column" # si la colonne dépend d'une autre colonne de la table, elle a un élément parent
            }, 
            ...
        ]
        
    """
    columns = ds.get_config().get('schema').get('columns')
    query = """SELECT"""
    for col in columns:
        col_name = col['name']
        query = query + ' count(distinct "%s") as "%s",'% (col_name, col_name)

    query = query[:-1] + """ FROM %s""" % table_name
    distinct_dict = executor.query_to_df(query).to_dict(orient="records")[0]
    for col in columns:
        # si la colonne a moins de 10 valeurs uniques et est de type string, on crée une liste déroulante
        if distinct_dict[col['name']] <= 10 and col['type']=='string':
            sub_query = """SELECT DISTINCT "{0}" as "{0}" FROM {1} """.format(col['name'], table_name)
            df = executor.query_to_df(sub_query)
            uniques = df[col['name']].tolist()
            col['uniques'] = uniques
            col['type'] = 'categorical'
        
        
        
        # Ici je définis à la main des colonnes qui ont des relations parent / child 
        if col['name']=='Outlet_Location_Type':
            col['child'] = 'Outlet_Identifier'
        
        if col['name']=='Outlet_Identifier':
            col['parent'] = 'Outlet_Location_Type'
    
    return json.dumps({'columns':columns})


@app.route('/get_dropdown_values/<path:params>')
def get_dropdown_values(params):
    """
        Cette fonction récupère les valeurs uniques d'une colonne child à partir de la valeur sélectionnée dans la colonne parent
        pour ensuite les ajouter à la liste déroulante
    """
    variables = json.loads(params)
    parent = variables['parent']
    child = variables['child']
    value = variables['selected']
    
    query = """ SELECT DISTINCT "{0}" as "a"
    FROM {1}
    WHERE "{2}" = '{3}'
    """.format(child, table_name, parent, value)
    print(query)
    df = executor.query_to_df(query)
    data = df['a'].tolist()
    
    return json.dumps({'data':data})


@app.route('/write_row', methods = ['POST'])
def write_row():
    """
        Cette fonction récupère les données entrées dans le formulaire et les écrit dans la table
    """
    row_dict = json.loads(request.get_data()).get('row')
    
    try :
        col_list = ['"%s"' % col for col in row_dict.keys()]
        cols = ', '.join(col_list)
        vals = ', '.join([repr(str(value)) for value in row_dict.values()])
        executor = SQLExecutor2(connection=connection_name)
        pre_query="""INSERT INTO %s (%s)
            VALUES (%s);
            COMMIT;
            """ %(table_name, cols, vals)
        df = executor.query_to_df( """select * from %s
            limit 1
            """ % table_name, pre_queries=[pre_query])
        df.to_csv("changes.csv", mode="a", header=False, index=False) # TODO: use Dataiku API and Dataset to write change log
        return json.dumps({'status':'ok'})
    except Exception as e:
        print(e)
        return json.dumps({'status':'error'})

