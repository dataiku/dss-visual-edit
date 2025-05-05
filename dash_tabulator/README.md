# dash_tabulator

`dash_tabulator` is a data table component for the [Dash](https://dash.plotly.com/) Python webapp framework, based on [Tabulator.js](http://tabulator.info) and used by the [Visual Edit webapp](../dss-plugin-visual-edit/README.md).

Being a Dash component, it comes as a Python module that includes a `DashTabulator.py` class and minified Javascript code used by Dash to make the component work. Both are generated from the React component’s source code in `DashTabulator.react.js`, by `webpack` and `dash-generate-components` (a Python CLI).

## Install dependencies

### Python

* Pre-requisite: install pyenv-virtualenv. On a Mac:

```bash
brew install pyenv pyenv-virtualenv
```

* Create and activate a Python virtual environment (we use the same Python version as for the Visual Edit plugin, for simplicity):

```bash
pyenv virtualenv 3.9.19 dash_tabulator
pyenv activate dash_tabulator
```

* Install packages:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### JS

* Pre-requisite: install node 21.2.0 and webpack. On a Mac:

```bash
brew install node webpack
```

* Install packages (going into `node_modules/`):

```bash
npm install
```

## Build node project

* Reinstall JS dependencies when modifying `packages.json` (for instance when upgrading packages such as Tabulator), and Python dependencies when modifying `requirements.txt` (this should happen much less frequently).

* Build the node project whenever making changes to the React component's source code. The build command defined in `packages.json` uses:
  * `webpack` to bundle all JS code (node modules from above and JS part of the Dash component) into `dash_tabulator.min.js` (or `.dev.js` when using webpack with `--mode development`)
  * `dash-generate-components` to create the `DashTabulator.py` file and class, to be imported in a Dash webapp; this uses Python, hence the importance of activating the proper Python environment beforehand.

```bash
pyenv activate 3.9.19/envs/dash_tabulator
npm run build
```

* Copy built component (in `dash_tabulator/`) to Visual Edit's Python library:

```bash
npm run postbuild
```

### Known errors (non-blocking)

* If you hit an ERR_OSSL_EVP_UNSUPPORTED error while building the node project, it is likely due to [this](https://stackoverflow.com/a/70582385)
Run `NODE_OPTIONS=--openssl-legacy-provider npm run build` instead.
* Errors when building dash_tabulator at line 79 of dash.development.component_generator.py. This executes a `node` command which fails (dash.extract_meta.js, around lines 137 and 172). Use debug config in VS Code to find out more.

## Testing

The project includes unit tests to ensure the reliability of key functionality, such as the `extractFilterValues` utility function used for processing single-select and multi-select filter events from dataiku native dashboard filters in `DashTabulator.react.js`. Tests are written using [Jest](https://jestjs.io/).

### Setup

1. **Install Testing Dependencies**:
   Ensure all dependencies are installed by running:
   ```bash
   npm install
   ```

2. **Configuration**:
   The project includes Babel configuration in `.babelrc` to support ES modules, JSX, and a browser-like environment (via `jsdom`).

3. **Test Files**:
   Unit tests are located in `src/**/*.test.*`

### Running Tests

```bash
npm test
```

## React component walkthrough

The component code is in `src/lib/components/DashTabulator.react.js`. Tabulator is wrapped into a React component, taking in properties that match those of the Dash component in Python: `id`, `data`, `columns`, `datasetName`, `groupBy`, `setProps`, and `cellEdited`.

### Instantiating Tabulator

Simple examples of Tabulator in vanilla JS can be found in `tabulator_examples/`.

When the React component mounts, in `DashTabulator.react.js`, it creates a new instance of the Tabulator library with the given `data`, `columns`, and `groupBy` props. It also sets several options for the table, such as `selectable`, `layout`, `pagination`, `movableColumns`, and `persistence`.

The `columns` prop can include references to JavaScript functions defined in `assets/custom_tabulator.js`, which make it easy to customize the data table powered by Tabulator:

* `minMaxFilterFunction` and `minMaxFilterEditor` add a min/max filter to numerical columns
* `headerMenu` adds a "Hide" and "Group by" menu to columns, which appears when right-clicking on the column header
* `itemFormatter` formats items that appear when editing a column with type "list"; if those items are objects with `value`, `label`, and other properties, the label will be shown in bold and other properties will be shown in a new line below the label. This is used for "linked record" columns in Visual Edit's Webapp.

### Callback on cell edited

One important feature of `DashTabulator.react.js` is that it includes a callback for when a cell is edited. When this happens, the `cellEdited` prop is updated with information about the edited cell, including the field name, the editor type, the initial value, the old value, the new value, and the row data. The `cellEdited` prop is then passed to the `setProps` function, which updates the component's properties and triggers any relevant callbacks. As a result, this information is made available when defining callbacks on `cellEdited` in a Dash application that uses `DashTabulator.py`.

### Styling

We use Tabulator's Semantic UI theme and define additional CSS styles in `assets/tabulator_dataiku.css`.

### Tracking user interactions

The React component also includes some additional functionality for tracking user interactions with the table. For example, when the component is rendered, it requests WT1 to log an event indicating that the data table was displayed; this request is then processed according to your tracking preferences (at the level of your Dataiku instance).

* The `visualedit-display-table` event has the following properties:
  * `dataset_name_hash`
  * `rows_count`
  * `columns_hashed`
  * `plugin_version`
* The `visualedit-edit-cell` event has the following properties:
  * `dataset_name_hash`
  * `column_name_hash`
  * `column_type`
  * `plugin_version`

### Inspiration

Our component code is a simplified version of what's available in the public [dash_tabulator](https://github.com/preftech/dash-tabulator) package. The latter uses a react-tabulator library which hasn't been updated to the latest versions of Tabulator. Example usage can be found in [this CodeSandbox](https://codesandbox.io/s/react-tabulator-examples-forked-oif3d9?file=/src/components/Home.js).

## Original content from boilerplate

This project was originally generated by the [dash-component-boilerplate](https://github.com/plotly/dash-component-boilerplate) with the following settings:

* project_name: dash_tabulator
* github_org: dataiku
* description: Tabulator component for Dash
* Select use_async: False
* publish_on_npm: False
* install_dependencies: False

Javascript dependencies are listed in `package.json`: it includes `dash-extensions`, and we added the latest version of `tabulator-tables`.

### Original instructions

- The demo app is in `src/demo` and you will import your example component code into your demo app.
- Test your code in a Python environment:
    1. Build your code
        ```
        $ npm run build
        ```
    2. Run and modify the `usage.py` sample dash app:
        ```
        $ python usage.py
        ```
- Write tests for your component.
    - A sample test is available in `tests/test_usage.py`, it will load `usage.py` and you can then automate interactions with selenium.
    - Run the tests with `$ pytest tests`.
    - The Dash team uses these types of integration tests extensively. Browse the Dash component code on GitHub for more examples of testing (e.g. https://github.com/plotly/dash-core-components)
- Add custom styles to your component by putting your custom CSS files into your distribution folder (`dash_tabulator`).
    - Make sure that they are referenced in `MANIFEST.in` so that they get properly included when you're ready to publish your component.
    - Make sure the stylesheets are added to the `_css_dist` dict in `dash_tabulator/__init__.py` so dash will serve them automatically when the component suite is requested.
- [Review your code](./review_checklist.md)
- Create a production build and publish:
    1. Build your code:
        ```
        $ npm run build
        ```
    2. Create a Python distribution
        ```
        $ python setup.py sdist bdist_wheel
        ```
        This will create source and wheel distribution in the generated the `dist/` folder.
        See [PyPA](https://packaging.python.org/guides/distributing-packages-using-setuptools/#packaging-your-project)
        for more information.

    3. Test your tarball by copying it into a new environment and installing it locally:
        ```
        $ pip install dash_tabulator-0.0.1.tar.gz
        ```

    4. If it works, then you can publish the component to NPM and PyPI:
        1. Publish on PyPI
            ```
            $ twine upload dist/*
            ```
        2. Cleanup the dist folder (optional)
            ```
            $ rm -rf dist
            ```
        3. Publish on NPM (Optional if chosen False in `publish_on_npm`)
            ```
            $ npm publish
            ```
            _Publishing your component to NPM will make the JavaScript bundles available on the unpkg CDN. By default, Dash serves the component library's CSS and JS locally, but if you choose to publish the package to NPM you can set `serve_locally` to `False` and you may see faster load times._