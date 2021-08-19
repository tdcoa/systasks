select
 calendar_date as LogDate
,random(10,100) as random_value1
,random_value1 + random(-10,30) as random_value2
,random_value2 + random(-10,30) as random_value3
from sys_calendar.calendar
where LogDate between {{ startdate }} and {{ enddate }}
