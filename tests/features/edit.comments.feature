Feature: Visual Edit has special behavior for comments column.
    Background:
        Given the webapp "bodh8Xz" has the configuration from "./features/edit.comments.feature.json"

    @cleanup_projects
    Scenario Outline: Editing comments column alone creates one editlog.
        Given a managed dataset "products" on connection "<connection>"
            | string  | string    | string   | bool     | string   |
            | id      | company   | location | reviewed | comments |
            | Answers | BS plugin | fr       | false    |          |
            | DSS     | dku       | gaule    | false    |          |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | Answers             | comments      | my comment   |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key,column_name"
            | key     | user   | column_name | value      | action |
            | Answers | reader | comments    | my comment | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | location       | string |
            | reviewed       | string |
            | comments       | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id      | company | location | reviewed | comments   | last_action | first_action |
            | Answers |         |          |          | my comment | update      | update       |
        And the dataset "products_edited" has the following schema
            | name     | type    |
            | id       | string  |
            | company  | string  |
            | location | string  |
            | reviewed | boolean |
            | comments | string  |
        And the dataset "products_edited" contains the following using compound key "id"
            | id      | company   | location | reviewed | comments   |
            | Answers | BS plugin | fr       | false    | my comment |
            | DSS     | dku       | gaule    | false    |            |

        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |

    @cleanup_projects
    Scenario Outline: Editing comments and reviewed columns together creates one editlog for all editable columns except comment.
        Given a managed dataset "products" on connection "<connection>"
            | string  | string    | string   | bool     | string   |
            | id      | company   | location | reviewed | comments |
            | Answers | BS plugin | fr       | false    |          |
            | DSS     | dku       | gaule    | false    |          |
        And I start the webapp
        And I navigate to the webapp
        When I edit rows as such
            | primary_keys                          | primary_keys_values                  | edited_column | edited_value |
            | id,company,location,reviewed,comments | Answers,BS plugin,fr,true,my comment | reviewed      | true         |
        And I do a forced recursive build of dataset "products_edited"
        Then the dataset "products_editlog" contains the following using compound key "key,column_name"
            | key     | user   | column_name | value     | action |
            | Answers | reader | company     | BS plugin | update |
            | Answers | reader | location    | fr        | update |
            | Answers | reader | reviewed    | True      | update |
        And the dataset "products_edits" has the following schema
            | name           | type   |
            | id             | string |
            | company        | string |
            | location       | string |
            | reviewed       | string |
            | comments       | string |
            | last_edit_date | string |
            | last_action    | string |
            | first_action   | string |
        And the dataset "products_edits" contains the following using compound key "id"
            | id      | company   | location | reviewed | comments | last_action | first_action |
            | Answers | BS plugin | fr       | True     |          | update      | update       |
        And the dataset "products_edited" has the following schema
            | name     | type    |
            | id       | string  |
            | company  | string  |
            | location | string  |
            | reviewed | boolean |
            | comments | string  |
        And the dataset "products_edited" contains the following using compound key "id"
            | id      | company   | location | reviewed | comments |
            | Answers | BS plugin | fr       | true     |          |
            | DSS     | dku       | gaule    | false    |          |

        Examples:
            | connection         |
            | local_dku_pg       |
            | bs-bigquery        |
            | filesystem_managed |