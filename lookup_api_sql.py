from dataiku import Dataset
from os import getenv
from dataiku.core.sql import SQLExecutor2
from flask import Flask, request, jsonify

ds = Dataset(getenv("DS_NAME"), getenv("PROJECT_KEY"))
connection_name = ds.get_config()['params']['connection']
table_name = get_table_name(ds) # TODO: get this method from commons
executor = SQLExecutor2(connection=connection_name)
# df = ds.get_dataframe()
col = "part_number"
server = Flask(__name__)

@server.route("/part_numbers", methods=['GET', 'POST'])
def api_py_function():
    if request.method == 'POST':
        term = request.get_json().get("term")
    else:
        term = request.args.get('term', '')

    if (len(term)>=3):
        # filtered_df = df[df[col].str.contains(term, case=False)].head(100)
        query = f"""SELECT {col} FROM "{table_name}" WHERE "{col}" LIKE "{term}%" LIMIT 100""" # change for contains instead of equality (and case insensitive), and cap at 100 results
        filtered_df = executor.query_to_df(query)
        
        result = filtered_df[col].to_list()
        # in case we'd want to return several lookup columns (this would require processing on Tabulator's side with a custom formatter):
        # result = filtered_df[lookup_cols].to_dict("records")
        
        response = jsonify(result)
    else:
        response = jsonify({})
    
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
