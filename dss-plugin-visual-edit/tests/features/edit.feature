Feature: Test edition of a SQL dataset.
    Background:
        Given the webapp "bodh8Xz" has the configuration from "./features/edit.feature.json"

    @cleanup_projects
    Scenario: Edit two columns.
        Given a managed dataset "products" on connection "local_dku_pg"
            | string  | string    | string   |
            | name    | company   | location |
            | Answers | BS plugin | fr       |
            | DSS     | dku       | gaule    |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | name         | Answers             | company       | dataiku      |
            | name         | Answers             | location      | france       |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key,column_name"
            | key     | user   | column_name | value   | action |
            | Answers | reader | company     | dataiku | update |
            | Answers | reader | location    | france  | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | name           | string |
            | company        | string |
            | location       | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "name"
            | name    | company | location | last_action | first_action |
            | Answers | dataiku | france   | update      | update       |
        And the dataset "products_edited" has the following schema
            | name     | type   |
            | name     | string |
            | company  | string |
            | location | string |
        And the dataset "products_edited" contains the following using compound key "name"
            | name    | company | location |
            | Answers | dataiku | france   |
            | DSS     | dku     | gaule    |

    @cleanup_projects
    Scenario: One edit overrides the previous one.
        Given a managed dataset "products" on connection "local_dku_pg"
            | string  | string    | string   |
            | name    | company   | location |
            | Answers | BS plugin | fr       |
            | DSS     | dku       | gaule    |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | name         | Answers             | company       | dku          |
        And I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | name         | Answers             | company       | dataiku      |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key,value"
            | key     | user   | column_name | value   | action |
            | Answers | reader | company     | dku     | update |
            | Answers | reader | company     | dataiku | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | name           | string |
            | company        | string |
            | location       | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "name"
            | name    | company | location | last_action | first_action |
            | Answers | dataiku |          | update      | update       |
        And the dataset "products_edited" has the following schema
            | name     | type   |
            | name     | string |
            | company  | string |
            | location | string |
        And the dataset "products_edited" contains the following using compound key "name"
            | name    | company | location |
            | Answers | dataiku | fr       |
            | DSS     | dku     | gaule    |