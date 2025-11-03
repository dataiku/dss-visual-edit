Feature: Visual Edit works with a single INTEGER primary key.
    Background:
        Given the webapp "bodh8Xz" has the configuration from "./features/edit.singlePK.feature.json"

    @cleanup_projects
    Scenario Outline: Edit a string column.
        Given a managed dataset "products" on connection "<connection>"
            | int | string    |
            | id  | company   |
            | 10  | BS plugin |
            | 12  | dku       |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | 10                  | company       | dataiku      |
            | id           | 12                  | company       | dataiku      |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key | user   | column_name | value   | action |
            | 10  | reader | company     | dataiku | update |
            | 12  | reader | company     | dataiku | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id | company | last_action | first_action |
            | 10 | dataiku | update      | update       |
            | 12 | dataiku | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type   |
            | id      | bigint |
            | company | string |
        And the dataset "products_edited" contains the following using compound key "id"
            | id | company |
            | 10 | dataiku |
            | 12 | dataiku |

        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Edit an integer column.
        Given a managed dataset "products" on connection "<connection>"
            | int | int     |
            | id  | company |
            | 10  | 10      |
            | 12  | 11      |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | 10                  | company       | 42           |
            | id           | 12                  | company       | 42           |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key | user   | column_name | value | action |
            | 10  | reader | company     | 42    | update |
            | 12  | reader | company     | 42    | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id | company | last_action | first_action |
            | 10 | 42      | update      | update       |
            | 12 | 42      | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type   |
            | id      | bigint |
            | company | bigint |
        And the dataset "products_edited" contains the following using compound key "id"
            | id | company |
            | 10 | 42      |
            | 12 | 42      |


        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Edit a float column.
        Given a managed dataset "products" on connection "<connection>"
            | int | float   |
            | id  | company |
            | 10  | 10.0    |
            | 12  | 11.0    |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | 10                  | company       | 42.0         |
            | id           | 12                  | company       | 42.0         |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key | user   | column_name | value | action |
            | 10  | reader | company     | 42.0  | update |
            | 12  | reader | company     | 42.0  | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id | company | last_action | first_action |
            | 10 | 42.0    | update      | update       |
            | 12 | 42.0    | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type   |
            | id      | bigint |
            | company | double |
        And the dataset "products_edited" contains the following using compound key "id"
            | id | company |
            | 10 | 42.0    |
            | 12 | 42.0    |

        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Edit a boolean column.
        Given a managed dataset "products" on connection "<connection>"
            | int | boolean |
            | id  | company |
            | 10  | false   |
            | 12  | false   |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | 10                  | company       | true         |
            | id           | 12                  | company       | true         |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key | user   | column_name | value | action |
            | 10  | reader | company     | True  | update |
            | 12  | reader | company     | True  | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id | company | last_action | first_action |
            | 10 | True    | update      | update       |
            | 12 | True    | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type    |
            | id      | bigint  |
            | company | boolean |
        And the dataset "products_edited" contains the following using compound key "id"
            | id | company |
            | 10 | True    |
            | 12 | True    |

        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |