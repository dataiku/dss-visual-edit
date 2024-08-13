Feature: Visual Edit works with a single STRING primary key.
    Background:
        Given the webapp "bodh8Xz" has the configuration from "./features/edit.singlePK.feature.json"

    @cleanup_projects
    Scenario Outline: Edit a string column.
        Given a managed dataset "products" on connection "<connection>"
            | string  | string    |
            | id      | company   |
            | Answers | BS plugin |
            | DSS     | dku       |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | Answers             | company       | dataiku      |
            | id           | DSS                 | company       | dataiku      |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key     | user   | column_name | value   | action |
            | Answers | reader | company     | dataiku | update |
            | DSS     | reader | company     | dataiku | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id      | company | last_action | first_action |
            | Answers | dataiku | update      | update       |
            | DSS     | dataiku | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type   |
            | id      | string |
            | company | string |
        And the dataset "products_edited" contains the following using compound key "id"
            | id      | company |
            | Answers | dataiku |
            | DSS     | dataiku |
        Examples:
            | connection         |
            | local_dku_pg       |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Edit an integer column.
        Given a managed dataset "products" on connection "<connection>"
            | string  | int     |
            | id      | company |
            | Answers | 10      |
            | DSS     | 11      |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | Answers             | company       | 42           |
            | id           | DSS                 | company       | 42           |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key     | user   | column_name | value | action |
            | Answers | reader | company     | 42    | update |
            | DSS     | reader | company     | 42    | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id      | company | last_action | first_action |
            | Answers | 42      | update      | update       |
            | DSS     | 42      | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type   |
            | id      | string |
            | company | bigint |
        And the dataset "products_edited" contains the following using compound key "id"
            | id      | company |
            | Answers | 42      |
            | DSS     | 42      |
        Examples:
            | connection         |
            | local_dku_pg       |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Edit a float column.
        Given a managed dataset "products" on connection "<connection>"
            | string  | float   |
            | id      | company |
            | Answers | 10.0    |
            | DSS     | 11.0    |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | Answers             | company       | 42.0         |
            | id           | DSS                 | company       | 42.0         |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key     | user   | column_name | value | action |
            | Answers | reader | company     | 42.0  | update |
            | DSS     | reader | company     | 42.0  | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id      | company | last_action | first_action |
            | Answers | 42.0    | update      | update       |
            | DSS     | 42.0    | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type   |
            | id      | string |
            | company | double |
        And the dataset "products_edited" contains the following using compound key "id"
            | id      | company |
            | Answers | 42.0    |
            | DSS     | 42.0    |
        Examples:
            | connection         |
            | local_dku_pg       |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Edit a boolean column.
        Given a managed dataset "products" on connection "<connection>"
            | string  | boolean |
            | id      | company |
            | Answers | false   |
            | DSS     | false   |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | Answers             | company       | true         |
            | id           | DSS                 | company       | true         |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key     | user   | column_name | value | action |
            | Answers | reader | company     | True  | update |
            | DSS     | reader | company     | True  | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id      | company | last_action | first_action |
            | Answers | True    | update      | update       |
            | DSS     | True    | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type    |
            | id      | string  |
            | company | boolean |
        And the dataset "products_edited" contains the following using compound key "id"
            | id      | company |
            | Answers | True    |
            | DSS     | True    |
        Examples:
            | connection         |
            | local_dku_pg       |
            | filesystem_managed |