Feature: Only authorized user can edit.
    Background:
        Given the webapp "bodh8Xz" has the configuration from "./features/edit.authorization.feature.json"

    @cleanup_projects
    Scenario: Unauthorized user can not edit.
        Given a managed dataset "products" on connection "filesystem_managed"
            | string  | string    | string   |
            | id      | company   | location |
            | Answers | BS plugin | fr       |
            | DSS     | dku       | gaule    |
        And I start the webapp
        And I navigate to the webapp
        Then editing rows as such is unauthorized
            | primary_keys | primary_keys_values | edited_column | edited_value |
            | id           | Answers             | company       | dataiku      |
            | id           | Answers             | location      | france       |