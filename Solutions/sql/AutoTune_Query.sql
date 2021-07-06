/*----------------------------------------------------------------------------------------------------------*/
/*                                                                                                          */
/*  Vantage AutoTune                                                                                        */
/*                                                                                                          */
/*    Version 04.14 Build 2021-04-05                                                                        */
/*    Copyright 2008-2021 Teradata. All rights reserved.                                                    */
/*                                                                                                          */
/*----------------------------------------------------------------------------------------------------------*/
/*                                                                                                          */
/* Consumption Analytics Query For Preliminary Analysis Of Customer AutoTune Potential                      */
/*                                                                                                          */
/*----------------------------------------------------------------------------------------------------------*/


Locking Row For Access

SELECT Statistics_Type "Statistics Group"
      ,case Statistics_Type
            when '1. Summary'           then  case when t.TotalTables = 0 then 'Feature Not Used On This Platform'
                                                   when Number_Tables = 0 then 'Best Practice Statistics Are Good'
                                                   else trim((Number_Tables (float)) / t.TotalTables  * 100 (format 'zzz.99')) || '% of tables are missing Summary Statistics (No Statistics at All) ' || '(' ||   trim(Number_Tables (format 'zzzzzzzz9')) || ' Objects)'
                                                   end
            when '2. Partitions'        then  case when pt.TotalPart = 0  then 'Feature Not Used On This Platform'
                                                   when Number_Tables = 0 then 'Best Practice Statistics Are Good'
                                                   else trim((Number_Tables (float)) / pt.TotalPart   * 100 (format 'zzz.99')) || '% of tables with Partitions are missing Statistics on ' || trim(Missing_Statistics (format 'zzzzzzzz9')) || ' Partitioning Columns ' || '(' || trim(Number_Tables (format 'zzzzzzzz9')) || ' Objects)'
                                                   end
            when '3. Secondary Index'   then  case when si.TotalSI = 0    then 'Feature Not Used On This Platform'
                                                   when Number_Tables = 0 then 'Best Practice Statistics Are Good'
                                                   else trim((Number_Tables (float)) / si.TotalSI     * 100 (format 'zzz.99')) || '% of tables with Secondary Indexes are missing Statistics on ' || trim(Missing_Statistics (format 'zzzzzzzz9')) || ' Indexes ' || '(' ||trim(Number_Tables (format 'zzzzzzzz9')) || ' Objects)'
                                                   end
            when '4. Join Index'        then case when ji.TotalJI = 0     then 'Feature Not Used On This Platform'
                                                   when Number_Tables = 0 then 'Best Practice Statistics Are Good'
                                                  else trim((Number_Tables (float)) / ji.TotalJI     * 100 (format 'zzz.99')) || '% of Join Indexes are missing Statistics '  || '(' || trim(Number_Tables (format 'zzzzzzzz9')) || ' Objects)'
                                                  end
            when '5. Soft-RI'           then  case when sr.TotalSR = 0 then 'Feature Not Used On This Platform'
                                                   when Number_Tables = 0 then 'Best Practice Statistics Are Good'
                                                   else trim((Number_Tables (float)) / sr.TotalSR     * 100 (format 'zzz.99')) || '% of tables with Soft RI are missing Statistics on ' || trim(Missing_Statistics (format 'zzzzzzzz9')) || ' Parent And Child Columns ' || '(' || trim(Number_Tables (format 'zzzzzzzz9')) || ' Objects)'
                                                   end
            when '6. Temporal'          then  case when tt.TotalTemp = 0  then 'Feature Not Used On This Platform'
                                                   when Number_Tables = 0 then 'Best Practice Statistics Are Good'
                                                   else trim((Number_Tables (float)) / tt.TotalTemp   * 100 (format 'zzz.99')) || '% of Temporal tables are missing Statistics on ' || trim(Missing_Statistics (format 'zzzzzzzz9')) || ' Begin/End Period Columns ' || '(' || trim(Number_Tables (format 'zzzzzzzz9')) || ' Objects)'
                                                   end
            end (VarChar(120)) Description

From
(
SELECT GroupKey.Statistics_Type
      ,Count(distinct DT.DatabaseName) Number_Databases
      ,Count(distinct DT.DatabaseName || Tablename ) Number_Tables
      ,Count(DT.ColumnName) Missing_Statistics

From
(
Select '1. Summary'         (VarChar(30)) Statistics_Type From dbc.dbcinfov Where infokey = 'version'
union
Select '2. Partitions'      (VarChar(30)) Statistics_Type From dbc.dbcinfov Where infokey = 'version'
union
Select '3. Secondary Index' (VarChar(30)) Statistics_Type From dbc.dbcinfov Where infokey = 'version'
union
Select '4. Join Index'      (VarChar(30)) Statistics_Type From dbc.dbcinfov Where infokey = 'version'
union
Select '5. Soft-RI'         (VarChar(30)) Statistics_Type From dbc.dbcinfov Where infokey = 'version'
union
Select '6. Temporal'        (VarChar(30)) Statistics_Type From dbc.dbcinfov Where infokey = 'version'
) GroupKey

Left Outer Join
(

SELECT '1. Summary' (VarChar(30)) Statistics_Type
      ,'*'            ColumnName
      ,t.DatabaseName DatabaseName
      ,t.TableName    TableName

From dbc.tablesV t

LEFT OUTER JOIN DBC.StatsV s
ON t.DatabaseName = s.DatabaseName
And t.TableName = s.TableName
And s.statsid = 0

Where t.DatabaseName LIKE '%'
  And t.TableName    LIKE '%'
  And t.tablekind IN ('T','O','I')
  And (SELECT CAST(SUBSTR(INFODATA,1,5) as DECIMAL(4,2)) VERSION From DBC.DBCINFOV Where INFOKEY = 'VERSION') >= 14.00

  And s.TableName IS NULL

--  And 'Y' = (SELECT ControlValue (char(01)) From AutoTune_Tables.AutoTune_Control Where ControlType = 999) -- Use Summary Statistics by Default

GROUP BY 1,2,3,4

UNION

SELECT '3. Primary Index'  (VarChar(30)) Statistics_Type
      ,ColumnLIST            ColumnName
      ,DatabaseName DatabaseName
      ,TableName    TableName

FROM
(
SELECT pti.DatabaseName
      ,pti.TableName
      ,IndexNumber
      ,IndexType
      ,td_sysfnlib.oreplace(TRIM(TRAILING ',' From (XMLAGG(TRIM(pti.ColumnName) || ',' ORDER BY pti.ColPos) (VARCHAR(1000)))),' ','') ColumnLIST

  FROM
(
    SELECT DatabaseName,
           TableName,
           IndexNumber,
           IndexType,
           ColumnName,
           ROW_NUMBER () OVER (partition BY DatabaseName, TableName, INDEXnumber ORDER BY DatabaseName, TableName, INDEXnumber, ColumnPosition) ColPos

      From DBC.IndicesV t

Where t.DatabaseName LIKE '%'
  And t.TableName    LIKE '%'
  And indextype IN ('K','P','Q')

) pti

GROUP BY 1,2,3,4
-- ORDER BY 1,2,3,4
) dt

Where (dt.DatabaseName, dt.TableName, td_sysfnlib.oreplace('"' || td_sysfnlib.oreplace(td_sysfnlib.oreplace(dt.columnlist,' ',''),',','","') || '"','""','"')) NOT IN
(
SELECT DatabaseName,
       TableName,
       td_sysfnlib.oreplace('"' || td_sysfnlib.oreplace(td_sysfnlib.oreplace(ColumnName,' ',''),',','","') || '"','""','"')
 From DBC.StatsV
Where DatabaseName LIKE '%'
  And TableName    LIKE '%'
  And ColumnName IS NOT NULL
)

 And (SELECT CAST(SUBSTR(INFODATA,1,5) as DECIMAL(4,2)) VERSION From DBC.DBCINFOV Where INFOKEY = 'VERSION') < 14.00  -- PIs prior to 14 else summary stats used

UNION

SELECT (CASE WHEN indextype IN ('1','2')
             THEN '4. Join Index'
             ELSE '3. Secondary Index'
             END) (VarChar(30)) Statistics_Type
      ,ColumnLIST            ColumnName
      ,DatabaseName DatabaseName
      ,TableName    TableName

FROM
(
SELECT pti.DatabaseName
      ,pti.TableName
      ,IndexNumber
      ,IndexType
      ,td_sysfnlib.oreplace(TRIM(TRAILING ',' From (XMLAGG(TRIM(pti.ColumnName) || ',' ORDER BY pti.ColPos) (VARCHAR(1000)))),' ','') ColumnLIST

  FROM
(
    SELECT DatabaseName,
           TableName,
           IndexNumber,
           IndexType,
           ColumnName,
           ROW_NUMBER () OVER (partition BY DatabaseName, TableName, INDEXnumber ORDER BY DatabaseName, TableName, INDEXnumber, ColumnPosition) ColPos

      From DBC.IndicesV t

Where t.DatabaseName LIKE '%'
  And t.TableName    LIKE '%'
  And indextype NOT IN ('K','P','Q','J')

) pti

GROUP BY 1,2,3,4
-- ORDER BY 1,2,3,4
) dt

Where (dt.DatabaseName, dt.TableName, td_sysfnlib.oreplace('"' || td_sysfnlib.oreplace(td_sysfnlib.oreplace(dt.columnlist,' ',''),',','","') || '"','""','"')) NOT IN
(
SELECT DatabaseName,
       TableName,
       td_sysfnlib.oreplace('"' || td_sysfnlib.oreplace(td_sysfnlib.oreplace(ColumnName,' ',''),',','","') || '"','""','"')
  From DBC.StatsV t
 Where t.DatabaseName LIKE '%'
   And t.TableName    LIKE '%'
   And ColumnName IS NOT NULL
)

UNION

SELECT '2. Partitions'  (VarChar(30)) Statistics_Type
      ,'partition'              ColumnName
      ,DA.DatabaseName DatabaseName
      ,DA.TableName    TableName

FROM
(
Select c.DatabaseName,
       c.TableName,
       case when ColumnPartitionNumber = 0 then 'partition' else 'partition#L1' end ColumnName

 From dbc.ColumnsV c

Where c.DatabaseName LIKE '%'
  And c.TableName    LIKE '%'

  And c.partitioningColumn = 'Y'
--  And c.ColumnType Not In ('UT', 'PD', 'PM', 'PS', 'PT', 'PZ','BO','CO') -- ignore column types that cannot have statistics

GROUP BY 1,2,3
) DA

LEFT OUTER JOIN DBC.StatsV s
  on DA.DatabaseName = s.DatabaseName
 And DA.TableName = s.TableName
 And DA.ColumnName = td_sysfnlib.oreplace(s.ColumnName,'"','')

Where s.ColumnName IS NULL

UNION

SELECT '2. Partitions'  (VarChar(30)) Statistics_Type
      ,DA.ColumnName ColumnName
      ,DA.DatabaseName     DatabaseName
      ,DA.TableName        TableName

From dbc.ColumnsV DA

LEFT OUTER JOIN DBC.StatsV s
  on DA.DatabaseName = s.DatabaseName
 And DA.TableName = s.TableName
 And DA.ColumnName = td_sysfnlib.oreplace(s.ColumnName,'"','')

Where DA.DatabaseName LIKE '%'
  And DA.TableName    LIKE '%'

  And DA.partitioningColumn = 'Y'
  And DA.ColumnType Not In ('UT', 'PD', 'PM', 'PS', 'PT', 'PZ','BO','CO') -- ignore column types that cannot have statistics

  And s.ColumnName IS NULL

UNION

SELECT '2. Partitions'  (VarChar(30)) Statistics_Type
      ,DA.ColumnLIST                ColumnName
      ,DA.DatabaseName     DatabaseName
      ,DA.TableName        TableName

FROM
(
SELECT pi.ColumnLIST
      ,pi.DatabaseName
      ,pi.TableName

FROM
(
SELECT pti.DatabaseName
      ,pti.TableName
      ,IndexNumber
      ,IndexType
      ,td_sysfnlib.oreplace(TRIM(TRAILING ',' From (XMLAGG(TRIM(pti.ColumnName) || ',' ORDER BY pti.ColPos) (VARCHAR(1000)))),' ','') ColumnLIST

  FROM
(
    SELECT DatabaseName,
           TableName,
           IndexNumber,
           IndexType,
           ColumnName,
           ROW_NUMBER () OVER (partition BY DatabaseName, TableName, INDEXnumber ORDER BY DatabaseName, TableName, INDEXnumber, ColumnPosition) ColPos

      From DBC.IndicesV t

Where t.DatabaseName LIKE '%'
  And t.TableName    LIKE '%'
  And indextype IN ('Q')
)  pti

GROUP BY 1,2,3,4
) pi

LEFT OUTER JOIN
(
-- grab partitioning Column

SELECT DA.DatabaseName,
       DA.TableName,
       DA.ColumnName

From dbc.ColumnsV DA

LEFT OUTER JOIN DBC.StatsV s
  on DA.DatabaseName = s.DatabaseName
 And DA.TableName = s.TableName
 And DA.ColumnName = td_sysfnlib.oreplace(s.ColumnName,'"','')

Where DA.DatabaseName LIKE '%'
  And DA.TableName    LIKE '%'
  And DA.partitioningColumn = 'Y'
  And DA.ColumnType Not In ('UT', 'PD', 'PM', 'PS', 'PT', 'PZ','BO','CO') -- ignore column types that cannot have statistics

) pc
 on pi.DatabaseName = pc.DatabaseName
And pi.TableName = pc.TableName
And POSITION(  pc.ColumnName   IN   pi.ColumnLIST  ) > 0

Where pc.TableName IS NULL

) DA

LEFT OUTER JOIN DBC.StatsV s
  on DA.DatabaseName = s.DatabaseName
 And DA.TableName = s.TableName
 And ('partition,' || DA.columnlist) = td_sysfnlib.oreplace(s.ColumnName,'"','')

Where s.ColumnName IS NULL

UNION

SELECT '6. Temporal'  (VarChar(30)) Statistics_Type
      ,DA.ColumnName            ColumnName
      ,DA.DatabaseName DatabaseName
      ,DA.TableName    TableName

FROM
(
SELECT c.DatabaseName,
       c.TableName,
       c.ColumnName,
       'BEGIN(' || TRIM(c.ColumnName)   || ')' NewColumnName,
       'BEGIN_' || TRIM(c.ColumnName) NewStatsName

From dbc.tablesV t,
     dbc.ColumnsV c

Where t.tablekind IN ('T','O','I')
  And t.DatabaseName = c.DatabaseName
  And t.TableName    = c.TableName
  And t.DatabaseName LIKE '%'
  And t.TableName    LIKE '%'

  And c.columntype In ('PM','PS')

  And (c.DatabaseName, c.TableName, NewColumnName) not iN
  (
   SELECT DatabaseName, TableName, td_sysfnlib.oreplace(ColumnName,' ','') ColumnName
     From dbc.StatsV
   Where ColumnName like 'BEGIN(%'
     And DatabaseName LIKE '%'
     And TableName    LIKE '%'
  )

  And (c.DatabaseName, c.TableName, c.ColumnName) not iN
  (
   SELECT DatabaseName, TableName, ColumnName
     From dbc.StatsV
   Where DatabaseName LIKE '%'
     And TableName    LIKE '%'
  )

  And (c.DatabaseName, c.TableName, NewStatsName) not iN
  (
   SELECT DatabaseName, TableName, ColumnName
     From dbc.ColumnsV
   Where DatabaseName LIKE '%'
     And TableName    LIKE '%'
  )

) DA

UNION

SELECT '6. Temporal'  (VarChar(30)) Statistics_Type
      ,DA.ColumnName            ColumnName
      ,DA.DatabaseName DatabaseName
      ,DA.TableName    TableName

FROM
(
SELECT c.DatabaseName,
       c.TableName,
       c.ColumnName,
       'END(' || TRIM(c.ColumnName)   || ')' NewColumnName,
       'END_' || TRIM(c.ColumnName) NewStatsName

From dbc.tablesV t,
     dbc.ColumnsV c

Where t.tablekind IN ('T','O','I')
  And t.DatabaseName = c.DatabaseName
  And t.TableName    = c.TableName
  And t.DatabaseName LIKE '%'
  And t.TableName    LIKE '%'

  And c.columntype In ('PM','PS')

  And (c.DatabaseName, c.TableName, NewColumnName) not iN
  (
   SELECT DatabaseName, TableName, td_sysfnlib.oreplace(ColumnName,' ','') ColumnName
     From dbc.StatsV
   Where ColumnName like 'END(%'
     And DatabaseName LIKE '%'
     And TableName    LIKE '%'
  )

  And (c.DatabaseName, c.TableName, c.ColumnName) not iN
  (
   SELECT DatabaseName, TableName, ColumnName
     From dbc.StatsV
   Where DatabaseName LIKE '%'
     And TableName    LIKE '%'
  )

  And (c.DatabaseName, c.TableName, NewStatsName) not iN
  (
   SELECT DatabaseName, TableName, ColumnName
     From dbc.ColumnsV
   Where DatabaseName LIKE '%'
     And TableName    LIKE '%'
  )

) DA

UNION

SELECT '5. Soft-RI'  (VarChar(30)) Statistics_Type
      ,child_columnlist  ColumnName
      ,ChildDB           DatabaseName
      ,ChildtABLE        TableName

FROM
(
SELECT  ChildDB
       ,ChildTable
       ,td_sysfnlib.oreplace(TRIM(TRAILING ',' From (XMLAGG(TRIM(ChildKeyColumn) || ',' ORDER BY ColumnPosition) (VARCHAR(1000)))),' ','') child_columnlist

       ,ParentDB
       ,ParentTable
       ,td_sysfnlib.oreplace(TRIM(TRAILING ',' From (XMLAGG(TRIM(ParentKeyColumn) || ',' ORDER BY ColumnPosition) (VARCHAR(1000)))),' ','') parent_columnlist

       ,IndexId

FROM
(
SELECT RANK() OVER (partition BY ChildDB, ChildTable, IndexId ORDER BY ChildDB, ChildTable, IndexId, Columnid ) ColumnPosition,

       ChildDB,
       ChildTable,
       ChildKeyColumn,

       ParentDB,
       ParentTable,
       ParentKeyColumn,

       IndexId

From dbc.all_ri_childrenV r,
     dbc.ColumnsV c

Where childdb     LIKE '%'
  And ChildTable  LIKE '%'

  And childdb = c.DatabaseName
  And childtable = c.TableName
  And childkeycolumn = c.ColumnName

) dt

GROUP BY 1,2,4,5,7

) dt2

LEFT OUTER JOIN DBC.StatsV s
  on dt2.childdb = s.DatabaseName
 And dt2.childtable = s.TableName
 And dt2.child_columnlist = td_sysfnlib.oreplace(s.ColumnName,'"','')

Where dt2.childdb LIKE '%'

And s.ColumnName IS NULL

GROUP BY 1,2,3,4

UNION

SELECT '5. Soft-RI'  (VarChar(30)) Statistics_Type
      ,parent_columnlist  ColumnName
      ,ParentDB           DatabaseName
      ,ParenttABLE        TableName

FROM
(

SELECT  ChildDB
       ,ChildTable
       ,td_sysfnlib.oreplace(TRIM(TRAILING ',' From (XMLAGG(TRIM(ChildKeyColumn) || ',' ORDER BY ColumnPosition) (VARCHAR(1000)))),' ','') child_columnlist

       ,ParentDB
       ,ParentTable
       ,td_sysfnlib.oreplace(TRIM(TRAILING ',' From (XMLAGG(TRIM(ParentKeyColumn) || ',' ORDER BY ColumnPosition) (VARCHAR(1000)))),' ','') parent_columnlist

	  ,IndexId

FROM
(
SELECT RANK() OVER (partition BY ChildDB, ChildTable, IndexId ORDER BY ChildDB, ChildTable, IndexId, Columnid ) ColumnPosition,

       ChildDB,
       ChildTable,
       ChildKeyColumn,

       ParentDB,
       ParentTable,
       ParentKeyColumn,

       IndexId

From dbc.all_ri_childrenV r,
     dbc.ColumnsV c

Where childdb     LIKE '%'
  And childtable  LIKE '%'

  And childdb = c.DatabaseName
  And childtable = c.TableName
  And childkeycolumn = c.ColumnName
) dt

GROUP BY 1,2,4,5,7
) dt2

LEFT OUTER JOIN DBC.StatsV s
  on dt2.Parentdb = s.DatabaseName
 And dt2.Parenttable = s.TableName
 And dt2.Parent_columnlist = td_sysfnlib.oreplace(s.ColumnName,'"','')

Where dt2.Parentdb LIKE '%'

And s.ColumnName IS NULL

GROUP BY 1,2,3,4

) DT
on DT.Statistics_Type = GroupKey.Statistics_Type

-- use this for in-tool testing

-- And DT.DatabaseName Not In (Select databasename From Autotune_Tables.AutoTune_Database_Exclusion_list)
-- And DT.TableName Not In (Select tablename From Autotune_Tables.AutoTune_Table_Exclusion_list)

-- use this for TCA runs

And DT.DatabaseName Not In
(select DatabaseName from vt_dim_tdinternal_databases)

Group by 1
) TCA

-- -------------------------------------------------
--  Total Number of Tables
-- -------------------------------------------------

Inner Join
(
Select count(*) TotalTables From dbc.TablesV Where TableKind in ('t','o') And DatabaseName Not In
(select DatabaseName from vt_dim_tdinternal_databases)
) t
on 1=1

-- -------------------------------------------------
--  Total Number of Partitioned Tables
-- -------------------------------------------------

Inner Join
(
Select count(distinct databasename||Tablename) TotalPart From dbc.ColumnsV Where PartitioningColumn = 'Y' And DatabaseName Not In
(select DatabaseName from vt_dim_tdinternal_databases)
) pt
on 1=1


-- -------------------------------------------------
--  Total Number of Secondary Index Tables
-- -------------------------------------------------

Inner Join
(
Select coalesce(count(distinct databasename||Tablename),0) TotalSI From dbc.indicesV Where DatabaseName Not In
(select DatabaseName from vt_dim_tdinternal_databases)
) si
on 1=1

-- -------------------------------------------------
--  Total Number of Join Indexes
-- -------------------------------------------------

Inner Join
(
Select coalesce(count(distinct databasename||Tablename),0) TotalJI From dbc.IndicesV Where indextype IN ('1','2') And DatabaseName Not In
(select DatabaseName from vt_dim_tdinternal_databases)
) ji
on 1=1

-- -------------------------------------------------
--  Total Number of Soft RI Tables
-- -------------------------------------------------

Inner Join
(
Select coalesce(count(Childdb||ChildTable),0) TotalSR From dbc.all_ri_childrenV Where Childdb Not In
(select DatabaseName from vt_dim_tdinternal_databases)
) sr
on 1=1

-- -------------------------------------------------
--  Total Number of Temporal Tables
-- -------------------------------------------------

Inner Join
(
Select coalesce(count(*),0) TotalTemp From dbc.TablesV Where TemporalProperty in ('t','v','b') And DatabaseName Not In
(select DatabaseName from vt_dim_tdinternal_databases)
) tt
on 1=1


Order by Statistics_Type
;
