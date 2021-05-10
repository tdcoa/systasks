# Tasklist

A Tasklist is a YAML document (file name must end with `.yaml`) that resides in a top-level directory of a *collection*. The YAML file containing a tasklist can optionally contain any [jinja constructs](https://jinja.palletsprojects.com/en/2.11.x/templates/).

Attributes:

Name          | Type  | Required? | Purpose
--------------|-------|:---------:|-------------------------
`description` | text  |    No     | Tasklist description
`version`     | text  |    No     | Tasklist version
`tasks`       | array |    Yes    | An ordered list of tasks

Notes:
- A tasklist must contain at least one task.
- `description` and `version` may be used for documentation but otherwise have no effect

# Tasks

A task is of a *type* and has *name*, an optional *connection target* and a specific task definition

Attributes:

Name      | Type | Required? | Purpose
----------|------|:---------:|---------------------------------------------
`name`    | text |    Yes    | A descriptive name. Recommended to be unique
`connect` | enum |    No     | Can be either *source* or *transcend*
*taskdef* | dict |    Yes    | Any of the supported task types

## execute

Run one SQL statement

Attributes:

Name      | Type | Required? | Purpose
----------|------|:---------:|--------------------------------------------
`sql`     | text |   Maybe   | SQL text. Mutually exclusive with `sqlfile`
`sqlfile` | path |   Maybe   | A file name that holds the SQL text

## export

Run one SQL statement, and save data to a file in CSV format

Attributes:

Name      | Type | Required? | Purpose
----------|------|:---------:|--------------------------------------------
`sql`     | text |   Maybe   | SQL text. Mutually exclusive with `sqlfile`
`sqlfile` | path |   Maybe   | A file name that holds the SQL text
`file`    | path |    Yes    | Output file name

## import

Read CSV formatted data and store the contents into the named table.
Notes:
- Table must exist
- Existing data is not cleared before inserting new data

Attributes:

Name    | Type | Required? | Purpose
--------|------|:---------:|-----------------------------
`file`  | path |    Yes    | Input file name
`table` | text |    Yes    | table name to load data into

## copy

Copy files from the input directory to the output directory

Attributes:

Name    | Type          | Required? | Purpose
--------|---------------|:---------:|-------------------------------
`files` | array of path |    Yes    | name of the files to be copied

## call

Call a stored procedure

Attributes:

Name     | Type  | Required? | Purpose
---------|-------|:---------:|----------------------------------------------------
`proc`   | text  |    Yes    | name of the stored-procedure
`params` | array |    No     | optional parameters to pass to the stored-procedure

## chart

Run an application, typically a python script, that creates a chart

Attributes:

Name      | Type  | Required? | Purpose
----------|-------|:---------:|-------------------------------------------
`command` | text  |    Yes    | name of the command (Python script name)
`params`  | array |    No     | optional parameters to pass to the command

## script

Run an application, typically a python script

Attributes:

Name      | Type  | Required? | Purpose
----------|-------|:---------:|-------------------------------------------
`command` | text  |    Yes    | name of the command (Python script name)
`params`  | array |    No     | optional parameters to pass to the command

## ppt

Build a PowerPoint from a template

Attributes:

Name   | Type | Required? | Purpose
-------|------|:---------:|------------------------------------
`file` | path |    Yes    | location of the PowerPoint template

# Built-ins

Built-in variables and functions are available globally in all jinja templates without being explicitly defined.

## dirs

`dirs` is an *object* that defines following attributes for static directory paths:
- `dirs.home`: User's home directory
- `dirs.cwd`: Application's current working directory
- `dirs.systasks`: Base directory that contains bundled system collections

## dbc

`dbc` is an *object* with attributes that evaluates *DBQL* table names dynamically depending on availability of PDCR support. Availability of PDCR can be overridden (default `true`) by defining `pdcr` variable for applicable source systems.

For example, *jinja expression* `{{ dbc.DBQLogTbl }}` evaluates to `PDCRInfo.DBQLogTbl_Hst` when PDCR is available, otherwise it'll evaluate to `dbc.DBQLogTbl`.

`dbc` object also has a special attribute `logdt`, and a function `logdate(<alias>)`. Jina expression `{{ dbc.logdt }}` evaluates to `LogDate` for systems that support PDCR, or `CAST(CollectTimeStamp AS DATE)` for systems that do not have PDCR support. While `logdt` is an attribute, `logdate()` is a function that allows using an *alias* within an expression. For example, `{{ dbc.logdate('A') }}` evaluates to `CAST(A.CollectTimeStamp AS DATE)`. Alias may be necessary if an unqualified reference to `CollectTimeStamp` is ambiguous.

### Short names

`dbc` object recognizes the following short-names and expands them to the corresponding long names. For example, `{{ dbc.sql }}` evaluates to either `dbc.DBQLSqlTbl` for `dbc`, or `PDCRInfo.DBQLSqlTbl_Hst` for `pdcr`


Short name | Long name
-----------|-----------------
`expl`     | `DBQLExplainTbl`
`obj`      | `DBQLObjTbl`
`log`      | `DBQLogTbl`
`param`    | `DBQLParamTbl`
`sql`      | `DBQLSqlTbl`
`step`     | `DBQLStepTbl`
`summary`  | `DBQLSummaryTbl`
`utility`  | `DBQLUtilityTbl`
`xmllock`  | `DBQLXMLLockTbl`
`xml`      | `DBQLXMLTbl`
`sawt`     | `ResUsageSawt`
`scpu`     | `ResUsageScpu`
`shst`     | `ResUsageShst`
`sldv`     | `ResUsageSldv`
`smhm`     | `ResUsageSmhm`
`spdsk`    | `ResUsageSpdsk`
`spma`     | `ResUsageSpma`
`sps`      | `ResUsageSps`
`svdsk`    | `ResUsageSvdsk`
`svpr`     | `ResUsageSvpr`

## pyformat

`pyformat` is *Jinja filter* which is aliased to Python's [`format()`](https://docs.python.org/3/library/functions.html#format) function. This filter behaves differently from Jinja's built-in filter [`format()`](https://jinja.palletsprojects.com/en/2.11.x/templates/#format).
