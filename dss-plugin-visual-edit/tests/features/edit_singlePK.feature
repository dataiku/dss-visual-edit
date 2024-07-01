Feature: SQL, single primary key.
    Background:
        Given an existing webapp "bodh8Xz" in project "VISUALEDITINTEGRATIONTESTS"
        And an emptied existing dataset named "products_editlog"
        And an emptied existing dataset named "products_edits"
        And an emptied existing dataset named "products_edited"

    Scenario: Edit a string column.
        Given an existing dataset named "products" with the following content
            | string  | string    |
            | name    | company   |
            | Answers | BS plugin |
            | DSS     | dku       |
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | name         | Answers             | company       | dataiku      |
            | name         | DSS                 | company       | dataiku      |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key     | column_name | value   | action |
            | Answers | company     | dataiku | update |
            | DSS     | company     | dataiku | update |
        And the dataset "products_edited" contains the following using compound key "name"
            | name    | company |
            | Answers | dataiku |
            | DSS     | dataiku |

    Scenario: Edit an integer column.
        Given an existing dataset named "products" with the following content
            | string  | int     |
            | name    | company |
            | Answers | 0       |
            | DSS     | 10      |
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | name         | Answers             | company       | 42           |
            | name         | DSS                 | company       | 42           |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key     | column_name | value | action |
            | Answers | company     | 42    | update |
            | DSS     | company     | 42    | update |
        And the dataset "products_edited" contains the following using compound key "name"
            | name    | company |
            | Answers | 42      |
            | DSS     | 42      |

    Scenario: Edit a float column.
        Given an existing dataset named "products" with the following content
            | string  | float   |
            | name    | company |
            | Answers | 0.1     |
            | DSS     | 10.2    |
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | name         | Answers             | company       | 42.0         |
            | name         | DSS                 | company       | 42           |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key     | column_name | value | action |
            | Answers | company     | 42.0  | update |
            | DSS     | company     | 42    | update |
        And the dataset "products_edited" contains the following using compound key "name"
            | name    | company |
            | Answers | 42.0    |
            | DSS     | 42      |

    Scenario: Edit a boolean column.
        Given an existing dataset named "products" with the following content
            | string  | boolean |
            | name    | company |
            | Answers | true    |
            | DSS     | false   |
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | name         | Answers             | company       | true         |
            | name         | DSS                 | company       | true         |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key     | column_name | value | action |
            | Answers | company     | true  | update |
            | DSS     | company     | true  | update |
        And the dataset "products_edited" contains the following using compound key "name"
            | name    | company |
            | Answers | true    |
            | DSS     | true    |