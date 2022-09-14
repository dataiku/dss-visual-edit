from dataiku import Dataset
from flask import Flask, request, jsonify
from os import getenv

ds = Dataset(getenv("DS_NAME"), getenv("PROJECT_KEY"))
df = ds.get_dataframe()
col = "part_number"
server = Flask(__name__)

@server.route("/part_numbers", methods=['GET', 'POST'])
def api_py_function():
    if request.method == 'POST':
        term = request.get_json().get("term")
    else:
        term = request.args.get('term', '')
    print("Received a request for term: " + term)

    if (len(term)>=3):
        filtered_df = df[df[col].str.contains(term, case=False)].head(100)
        
        result = filtered_df[col].to_list()
        # in case we'd want to return several lookup columns (this would require processing on Tabulator's side with a custom formatter):
        # result = filtered_df[lookup_cols].to_dict("records")
        
        response = jsonify(result)
    else:
        response = jsonify({})
    
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response
