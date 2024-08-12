Feature: Test edition of a SQL dataset with two composite keys.
    Background:
        Given the webapp "bodh8Xz" has the configuration from "./features/edit.multiPK.feature.json"

    @cleanup_projects
    Scenario: Edit a string column.
        Given a managed dataset "products" on connection "local_dku_pg"
            | float | string  | string    |
            | id    | name    | company   |
            | 10.1  | Answers | BS plugin |
            | 10.2  | DSS     | dku       |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id;name      | 10.1;Answers        | company       | dataiku      |
            | id;name      | 10.2;DSS            | company       | dataiku      |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key                 | user   | column_name | value   | action |
            | ('10.1', 'Answers') | reader | company     | dataiku | update |
            | ('10.2', 'DSS')     | reader | company     | dataiku | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | name           | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id,name"
            | id   | name    | company | last_action | first_action |
            | 10.1 | Answers | dataiku | update      | update       |
            | 10.2 | DSS     | dataiku | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type   |
            | id      | double |
            | name    | string |
            | company | string |
        And the dataset "products_edited" contains the following using compound key "id,name"
            | id   | name    | company |
            | 10.1 | Answers | dataiku |
            | 10.2 | DSS     | dataiku |