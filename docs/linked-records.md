# Setting up Linked Records

Define linked records to enforce a specific set of values for an editable column. The cell editor will be a dropdown widget.

The options to be presented in the dropdown must be defined in a "linked dataset". If this dataset doesn’t already exist, you can create it as an [Editable dataset](https://doc.dataiku.com/dss/latest/connecting/editable-datasets.html).

In the Visual Webapp settings, one of the editable columns should correspond to the primary key of the linked dataset.

See [here](data-table-features) for more information on the editing experience.

## Settings

- **Linked Dataset:** the name of the dataset containing the set of values to be displayed in the dropdown.
- **Column:** the column of the original dataset to be edited with the values of the linked dataset.
- **Primary Key:** the column name of the linked dataset primary key.
- **Label:** the column name of the linked dataset used to display the values in the dropdown (can be the primary key or any other columns).
- **Additional Lookups:** column names in the linked dataset giving more context to the label.

## Known limitations

- The linked dataset must have less than 1,000 records OR the linked dataset must be on an SQL connection.
- The storage type of the linked data set primary key must be of storage type **string** or **integer**.
- The maximum number of lookup columns is two.
- The linked dataset primary key and lookup columns values should not be empty.
- The linked dataset lookup columns should be different from the label column.
- If a lookup column is the same as the primary key column, then the lookup value will not be shown in the dropdown widget. Otherwise it will work as expected.

## Example

Given a dataset named PRODUCTS containing a list of products and another dataset named COMPANIES containing a list of companies, we want users of the web app to link products to a specific company.

***Original dataset***

| product_name  | company_name |
| ------------- | ------------- |
| DSS  |   |

***Dataset with linked records***

| company_name | industry |
| ------------- | ------------- |
| dataiku  | tech  |

The configuration could look like this:
- **Linked Dataset:** COMPANIES
- **Column:** company_id
- **Primary Key:** company_name
- **Label:** company_name
- **Additional Lookups:** industry

resulting in the following edited dataset one DSS is linked to dataiku.

***Original dataset edited (after building the flow)***

| product_name  | company_name |
| ------------- | ------------- |
| DSS  | dataiku   |

***Dataset with linked records***

| company_name | industry |
| ------------- | ------------- |
| dataiku  | tech  |