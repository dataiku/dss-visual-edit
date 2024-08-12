Feature: Test that first startup of Visual Edit webapp initializes the flow.
    @cleanup_projects
    Scenario: Editlog, edits and edited dataset are created with expected schema.
        Given a managed dataset "dataset" on connection "local_dku_pg"
            | string  | string    |
            | name    | company   |
            | Answers | BS plugin |
            | DSS     | dku       |
        And the webapp "bodh8Xz" has the configuration from "./features/flow.initialization.feature.json"
        When I start the webapp
        Then the dataset "dataset_editlog" has the following schema
            | name        | type   | meaning    |
            | date        | string | DateSource |
            | user        | string | Text       |
            | action      | string | Text       |
            | key         | string | Text       |
            | column_name | string | Text       |
            | value       | string | Text       |
        And the dataset "dataset_edits" has no schema
        And the dataset "dataset_edited" has no schema