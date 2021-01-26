create volatile table Feature_Usage as
(
    with dbql as (
      select
       dbq.LogDate
      ,dbq.featureusage
      ,usr.UserName
      ,usr.UserHash
      ,usr.User_Bucket
      ,usr.User_Department
      ,usr.User_SubDepartment
      ,usr.User_Region
      ,rec_count
      ,ampcputime
      from (
            select UserName
            ,{{dbc.logdt}} as LogDate
            ,featureusage
            ,count(*) as rec_count
            ,sum(ampcputime) as ampcputime
            from {{dbc.dbqlogtbl}}
            where LogDate between {{startdate}} and {{enddate}}
              and featureusage is not null
            group by UserName
            ,LogDate
            ,featureusage
            ) dbq
      join dim_user as usr
        on usr.UserName = dbq.UserName
    )
    select
     dbql.LogDate
    ,feat.featurename
    ,feat.featurebitpos as BitPos
    ,dbql.UserName
    ,dbql.UserHash
    ,dbql.User_Bucket
    ,dbql.User_Department
    ,dbql.User_SubDepartment
    ,dbql.User_Region
    ,sum(zeroifnull(dbql.rec_count)) as Query_Cnt
    ,sum(zeroifnull(dbql.ampcputime)) as AMPCPUTime
    from dbc.qrylogfeaturelistv feat
    join dbql
      on bytes(dbql.featureusage) = 256
     and getbit(dbql.featureusage,(2047-feat.featurebitpos)) = 1
    group by
    dbql.LogDate
   ,feat.featurename
   ,feat.featurebitpos
   ,dbql.UserName
   ,dbql.UserHash
   ,dbql.User_Bucket
   ,dbql.User_Department
   ,dbql.User_SubDepartment
   ,dbql.User_Region
) with data
  No Primary Index
  on commit preserve rows
