Feature: Simple SQL table edition.
    Background:
        Given an existing webapp "bodh8Xz" in project "VISUALEDITINTEGRATIONTESTS"
        And an existing dataset named "products" with the following content
            | string  | string    |
            | name    | company   |
            | Answers | BS plugin |
            | DSS     | dku       |
        And an emptied existing dataset named "products_editlog"
        And an emptied existing dataset named "products_edits"
        And an emptied existing dataset named "products_edited"

    Scenario: Edit one entry.
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