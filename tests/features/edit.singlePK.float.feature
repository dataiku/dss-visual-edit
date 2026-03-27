Feature: Visual Edit works with a single FLOAT primary key.
    Background:
        Given the webapp "bodh8Xz" has the configuration from "./features/edit.singlePK.feature.json"

    @cleanup_projects
    Scenario Outline: Edit a string column.
        Given a managed dataset "products" on connection "<connection>"
            | float | string    |
            | id    | company   |
            | 10.1  | BS plugin |
            | 10.2  | dku       |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | 10.1                | company       | dataiku      |
            | id           | 10.2                | company       | dataiku      |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key  | user   | column_name | value   | action |
            | 10.1 | reader | company     | dataiku | update |
            | 10.2 | reader | company     | dataiku | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id   | company | last_action | first_action |
            | 10.1 | dataiku | update      | update       |
            | 10.2 | dataiku | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type   |
            | id      | double |
            | company | string |
        And the dataset "products_edited" contains the following using compound key "id"
            | id   | company |
            | 10.1 | dataiku |
            | 10.2 | dataiku |

        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Edit an integer column.
        Given a managed dataset "products" on connection "<connection>"
            | float | int     |
            | id    | company |
            | 10.1  | 10      |
            | 10.2  | 11      |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | 10.1                | company       | 42           |
            | id           | 10.2                | company       | 42           |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key  | user   | column_name | value | action |
            | 10.1 | reader | company     | 42    | update |
            | 10.2 | reader | company     | 42    | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id   | company | last_action | first_action |
            | 10.1 | 42      | update      | update       |
            | 10.2 | 42      | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type   |
            | id      | double |
            | company | bigint |
        And the dataset "products_edited" contains the following using compound key "id"
            | id   | company |
            | 10.1 | 42      |
            | 10.2 | 42      |

        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Edit a float column.
        Given a managed dataset "products" on connection "<connection>"
            | float | float   |
            | id    | company |
            | 10.1  | 10.0    |
            | 10.2  | 11.0    |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | 10.1                | company       | 42.0         |
            | id           | 10.2                | company       | 42.0         |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key  | user   | column_name | value | action |
            | 10.1 | reader | company     | 42.0  | update |
            | 10.2 | reader | company     | 42.0  | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id   | company | last_action | first_action |
            | 10.1 | 42.0    | update      | update       |
            | 10.2 | 42.0    | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type   |
            | id      | double |
            | company | double |
        And the dataset "products_edited" contains the following using compound key "id"
            | id   | company |
            | 10.1 | 42.0    |
            | 10.2 | 42.0    |

        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Edit a boolean column.
        Given a managed dataset "products" on connection "<connection>"
            | float | boolean |
            | id    | company |
            | 10.1  | false   |
            | 10.2  | false   |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | 10.1                | company       | true         |
            | id           | 10.2                | company       | true         |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key"
            | key  | user   | column_name | value | action |
            | 10.1 | reader | company     | True  | update |
            | 10.2 | reader | company     | True  | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id   | company | last_action | first_action |
            | 10.1 | True    | update      | update       |
            | 10.2 | True    | update      | update       |
        And the dataset "products_edited" has the following schema
            | name    | type    |
            | id      | double  |
            | company | boolean |
        And the dataset "products_edited" contains the following using compound key "id"
            | id   | company |
            | 10.1 | True    |
            | 10.2 | True    |

        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |