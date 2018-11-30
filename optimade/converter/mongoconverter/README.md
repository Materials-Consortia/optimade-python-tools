# OPTIMade to MongoDB Converter
A converter that will take in a Lark tree and convert that to a MongoDB query

### Getting Started
1. Download project by running `git clone https://github.com/Materials-Consortia/optimade-python-tools`
2. `cd optimade-python-tools`
3. Install requirements by running `pip install -r requirements.txt` and `pip install -e .`
4. Now you should have mongoconverter installed as well as its dependency Lark, simply run `mongoconverter -h` for  help


#### Note
This is not a stand alone project, it depends on the `Parser` output from `optimade/filter.py`
