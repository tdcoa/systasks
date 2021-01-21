SELECT cast(cast(v.cal_date AS DATE) AS FORMAT 'YYYY-MM-DD')      AS cal_date
    , trim(v.item)                                                AS item
    , coalesce(c.year_of_calendar,extract(year from v.cal_date))  AS cal_year
    , cast(current_date AS FORMAT 'YYYY-MM-DD')                   AS today
FROM Sys_Calendar.Calendar   AS c
RIGHT OUTER JOIN valid_dates AS v
    ON c.calendar_date = v.cal_date;
