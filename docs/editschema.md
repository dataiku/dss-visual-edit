# Editschema

The editschema is a list of dictionaries in JSON format: one per column of the original dataset for which you want to provide additional settings.

## Example

```json
[
  {
    "name": "reviewed",
    "type": "boolean_tick"
  }
]
```

This example results in the following behavior:

![](boolean_tick.gif)

## Fields

List of available fields to describe each item of the editschema:

* `name`: name of a column of the original dataset.
* `type` allows to override the column's type inferred from the original dataset's schema, or to refine it:
  * You can specify a "boolean_tick" type if you want the formatting and editing of boolean values to use only 2 states: `true` represented by a green tick icon, and no icon at all otherwise.
  * Note: the default behavior of the "boolean" type uses 3 states: `true` represented by a green tick icon, `false` represented by a red cross, and empty.
