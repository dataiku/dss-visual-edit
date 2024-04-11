# Setting up Linked Records

Define linked records for columns where the editor should be a dropdown widget.

The options to be presented in the dropdown must be defined in a "linked dataset". If this dataset doesn’t already exist, you can create it as an Editable dataset.

In the Visual Webapp settings, one of the editable columns should correspond to the primary key of the linked dataset.

One of these two requirements must also be met: 1) the Linked Dataset must have less than 1,000 records; OR 2) the Linked Dataset must be on a SQL connection.

See [here](data-table-features) for more information on the editing experience.
