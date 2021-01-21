# Tasklist

A Tasklist is a YAML document (must have`.yaml` extension) that resides in a top-level directory of a *collection*. The YAML file containing a tasklist can optionally contain any jinja constructs.

Attributes:

| Name        | Type  | Required? | Purpose                  |
|-------------|-------|-----------|--------------------------|
| description | text  | No        | Tasklist description     |
| version     | text  | No        | Tasklist version         |
| tasks       | array | Yes       | An ordered list of tasks |

Note: A tasklist must contain at least one task

# Tasks

A task is of a *type* and has *name*, an optional *connection target* and a specific task definition

Attributes:

| Name      | Type | Required? | Purpose                                      |
|-----------|------|-----------|----------------------------------------------|
| name      | text | Yes       | A descriptive name. Recommended to be unique |
| connect   | enum | No        | Can be either *source* or *transcend*        |
| *taskdef* | dict | Yes       | Any of the supported task types              |

## execute

Run one SQL statement

Attributes:

| Name    | Type | Required? | Purpose                                     |
|---------|------|-----------|---------------------------------------------|
| sql     | text | Maybe     | SQL text. Mutually exclusive with `sqlfile` |
| sqlfile | path | Maybe     | A file name that holds SQL text             |

## export

Run one SQL statement, and save data to a file in CSV format

Attributes:

| Name    | Type | Required? | Purpose                                     |
|---------|------|-----------|---------------------------------------------|
| sql     | text | Maybe     | SQL text. Mutually exclusive with `sqlfile` |
| sqlfile | path | Maybe     | A file name that holds SQL text             |
| file    | path | Yes       | Output file name                            |

## import

Read CSV formatted data and store the contents into the named table.
Notes:
- Table must exist
- Existing data is not cleared before inserting new data

Attributes:

| Name  | Type | Required? | Purpose                      |
|-------|------|-----------|------------------------------|
| file  | path | Yes       | Input file name              |
| table | text | Yes       | table name to load data into |

## copy

Copy files from the input directory to the output directory

Attributes:

| Name  | Type          | Required? | Purpose                        |
|-------|---------------|-----------|--------------------------------|
| files | array of path | Yes       | name of the files to be copied |

## call

Call a stored procedure

Attributes:

| Name   | Type  | Required? | Purpose                                             |
|--------|-------|-----------|-----------------------------------------------------|
| proc   | text  | Yes       | name of the stored-procedure                        |
| params | array | No        | optional parameters to pass to the stored-procedure |

## chart

Run an application, typically a python script, that creates a chart

Attributes:

| Name    | Type  | Required? | Purpose                                    |
|---------|-------|-----------|--------------------------------------------|
| command | text  | Yes       | name of the command (Python script name)   |
| params  | array | No        | optional parameters to pass to the command |

## ppt

Build a PowerPoint from a template

Attributes:

| Name | Type | Required? | Purpose                             |
|------|------|-----------|-------------------------------------|
| file | path | Yes       | location of the PowerPoint template |

# Built-in Variables

Built-in variables are available globally without explicitly being defined.

## dbc

`dbc` is an *object* with attributes that evaluates *DBQL* table names dynamically depending on if PDCR support is available or not. For example, *jinja expression* `{{ dbc.DBQLogTbl }}` evaluates to `PDCRInfo.DBQLogTbl_Hst` if `pdcr` variable is set to `PDCR`, otherwise it'll evaluate to `dbc.DBQLogTbl`.

`dbc` object also has a special attribute `logdt`, and a function `logdate(<alias>)` that evaluates to either `CAST(CollectTimeStamp AS DATE)` or `LogDate` depending on if `pdcr` variable is set to `dbc` or `pdcr` respectively. While `logdt` is an attribute, `logdate()` is a function that allows prefixing the column name, within the evaluated expression, with an *alias*. For example, `{{ dbc.logdate('A') }}` evaluates to `CAST(A.CollectTimeStamp AS DATE)` which may be necessary if an unqualified reference to `CollectTimeStamp` is ambiguous.

### Short names

`dbc` object recognizes the following short-names and expands them to the corresponding long names. For example, `{{ dbc.sql }}` evaluates to either `dbc.DBQLSqlTbl` or `PDCRInfo.DBQLSqlTbl_Hst`.


| Short name | Long name        |
|------------|------------------|
| `expl`     | `DBQLExplainTbl` |
| `obj`      | `DBQLObjTbl`     |
| `log`      | `DBQLogTbl`      |
| `param`    | `DBQLParamTbl`   |
| `sql`      | `DBQLSqlTbl`     |
| `step`     | `DBQLStepTbl`    |
| `summary`  | `DBQLSummaryTbl` |
| `utility`  | `DBQLUtilityTbl` |
| `xmllock`  | `DBQLXMLLockTbl` |
| `xml`      | `DBQLXMLTbl`     |
| `sawt`     | `ResUsageSawt`   |
| `scpu`     | `ResUsageScpu`   |
| `shst`     | `ResUsageShst`   |
| `sldv`     | `ResUsageSldv`   |
| `smhm`     | `ResUsageSmhm`   |
| `spdsk`    | `ResUsageSpdsk`  |
| `spma`     | `ResUsageSpma`   |
| `sps`      | `ResUsageSps`    |
| `svdsk`    | `ResUsageSvdsk`  |
| `svpr`     | `ResUsageSvpr`   |
