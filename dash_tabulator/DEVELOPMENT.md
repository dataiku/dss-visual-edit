# Development

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
