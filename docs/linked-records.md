# Set up dropdown editing via "Linked Records"

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

- Linked dataset, if not on an SQL connection:
  - Only the first 10,000 records will be used.
  - If changes are made to the values in this dataset, the Visual Edit Webapp will need to be restarted in order to see the new values.
- Primary key column:
  - Must be unique within the linked dataset and not empty.
  - Storage type must be **string** or **integer**.
- When using lookup columns:
  - Label column should be different from primary key column.
  - Lookup columns should be different from the label column and from the primary key column.
  - Values should not be empty.
  - The maximum number of lookup columns is two.

## Example

Given a dataset named PRODUCTS containing a list of products and another dataset named COMPANIES containing a list of companies, we want users of the web app to link products to a specific company.

**_Original dataset_**

| product_name | company_name |
| ------------ | ------------ |
| DSS          |              |

**_Dataset with linked records_**

| company_name | industry |
| ------------ | -------- |
| dataiku      | tech     |

The configuration could look like this:

- **Linked Dataset:** COMPANIES
- **Column:** company_id
- **Primary Key:** company_name
- **Label:** company_name
- **Additional Lookups:** industry

resulting in the following edited dataset one DSS is linked to dataiku.

**_Original dataset edited (after building the flow)_**

| product_name | company_name |
| ------------ | ------------ |
| DSS          | dataiku      |

**_Dataset with linked records_**

| company_name | industry |
| ------------ | -------- |
| dataiku      | tech     |
