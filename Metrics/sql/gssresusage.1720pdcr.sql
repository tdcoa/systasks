/* THIS FILE HAS BEEN DE-MACRO-FIED BY AN AUTOMATED PROCESS. */
/*   Logic remains intact, but macro wrapper has been removed, */
/*   parameters have been changed to jinja template parameters, and */
/*   create volatile table wrapper has been added, to create an abstraction point. */

-- make dates more flexible: StartDate
{% set startdate = 'date-31' if startdate is not defined else startdate %}
{% if "date" in startdate.lower() %}
  -- Date looks like a SQL standard "DATE" or "Current_Date" function, no work needed
{% elif "select" in startdate.lower() %}
  -- Date looks like a SQL subselect, no work needed
{% elif "/" in startdate %}
  -- Date looks like a MM/DD/YYYY format, translating to 'YYYY-MM-DD' format
  {% set startmonth = ('00' ~ startdate.split("/")[0])[-2:] %}
  {% set startday   = ('00' ~ startdate.split("/")[1])[-2:] %}
  {% set startyear  = startdate.split("/")[2] %}
  {% set startdate  = "'" ~ startyear ~ "-" ~ startmonth ~ "-" ~ startday ~ "'" %}
{% elif "-" in startdate %}
  -- Date looks like a YYYY-MM-DD format, but reformatting just to be sure
  {% set startyear  = startdate.replace("'","").split("-")[0] %}
  {% set startmonth = ('00' ~ startdate.replace("'","").split("-")[1])[-2:] %}
  {% set startday   = ('00' ~ startdate.replace("'","").split("-")[2])[-2:] %}
  {% set startdate  = "'" ~ startyear ~ "-" ~ startmonth ~ "-" ~ startday ~ "'" %}
{% endif %}
-- startdate: {{ startdate }}

-- make dates more flexible: EndDate
{% set enddate = 'date-1' if enddate is not defined else enddate %}
{% if "date" in enddate.lower() %}
  -- Date looks like a SQL standard "DATE" or "Current_Date" function, no work needed
{% elif "select" in enddate.lower() %}
  -- Date looks like a SQL subselect, no work needed
{% elif "/" in enddate %}
  -- Date looks like a MM/DD/YYYY format, translating to 'YYYY-MM-DD' format
  {% set endmonth = ('00' ~ enddate.split("/")[0])[-2:] %}
  {% set endday   = ('00' ~ enddate.split("/")[1])[-2:] %}
  {% set endyear  = enddate.split("/")[2] %}
  {% set enddate  = "'" ~ endyear ~ "-" ~ endmonth ~ "-" ~ endday ~ "'" %}
{% elif "-" in startdate %}
  -- Date looks like a YYYY-MM-DD format, but reformatting just to be sure
  {% set endyear  = enddate.replace("'","").split("-")[0] %}
  {% set endmonth = ('00' ~ enddate.replace("'","").split("-")[1])[-2:] %}
  {% set endday   = ('00' ~ enddate.replace("'","").split("-")[2])[-2:] %}
  {% set enddate  = "'" ~ endyear ~ "-" ~ endmonth ~ "-" ~ endday ~ "'" %}
{% endif %}
-- enddate: {{ enddate }}

CREATE VOLATILE MULTISET TABLE vt_gssresusage_prework as (
/* gss_resusage_td1700-R006 */
sel
'TD17v1.0_PDCR' (named "Version")
,spma_dt.LogDate (named "LogDate")
,cast(spma_dt.LogDay as char(3)) (named "LogDOW")
,spma_dt.LogTime (named "LogTime")
,cast((spma_dt.LogDate || ' ' || spma_dt.LogTime) as timestamp(0)) (named "Timestamp")
,extract(hour from "Timestamp") (named "Hour")
,extract(minute from "Timestamp") / 10 * 10 (named "Minute10")
,SPMAInterval (named "RSSInterval")

/* System data */

,spma_dt.NodeType (Named "NodeGen")
,case when spma_dt.vproc1 > 0 then spma_dt.vproc1
 else 'PE-only Node'
end (Named "AMPS")
,spma_dt.NCPUs (Named "CPUs")
,cast(info.infodata as varchar(20)) (named "DBSRelease")

,PM_COD (Named "PMCOD")
,WM_COD (Named "WMCOD")
,IO_COD (Named "IOCOD")

,extract(minute from "Timestamp") (named "Minute01")
,extract(second from "Timestamp") (named "Seconds00")
,spma_dt.TDEnabledCPUs (named "ETcoreCPUs")
,diskspacev_dt.SumCurrPerm (named "SumCurrPerm")
,diskspacev_dt.SumMaxPerm (named "SumMaxPerm")
,diskspacev_dt.SumPeakSpool (named "SumPeakSpool")
,diskspacev_dt.SumPeakTemp (named "SumPeakTemp")

/*** end grouping fields ***/

,min(MemSizeGB) (Named "MinMemSizeGB")
,max(MemSizeGB) (Named "MaxMemSizeGB")
,count(distinct(spma_dt.NodeID)) (Named "NumNodes")

/* SPMA data */

,sum(CPUUtil) / NumNodes / CPUs / RSSInterval (format 'ZZ9.9') (named "AvgCPUBusy")
,max(CPUUtil) / CPUs / RSSInterval (format 'ZZ9.9') (named "MaxCPUBusy")
,sum(OSPctCPU) / NumNodes (format 'ZZ9.9') (named "AvgPctOSCPU")
,max(OSPctCPU)(format 'ZZ9.9') (named "MaxPctOSCPU")
,sum(IOWaitCPUUtil) / NumNodes / CPUs / RSSInterval (format 'ZZ9.9') (named "AvgPctIOWait")
,sum(RunQSz) / NumNodes (format 'z,zz9.9') (named "AvgRunQSz")
,max(MaxRunQSz) (format 'z,zz9.9') (named "MaxRunQSz")
,max(IOWaitCPUUtil) / CPUs / RSSInterval (format 'ZZ9.9') (named "MaxPctIOWait")
,zeroifnull( sum(SPMAPhysReads + SPMAPhysPreReads) /
nullifzero(sum(SPMAPhysReads + SPMAPhysPreReads + SPMAPhysWrites)) * 100) (format 'ZZ9.9') (named "PctReadsCnt")
,zeroifnull( sum(SPMAPhysReadKB + SPMAPhysPreReadKB) /
nullifzero(sum(SPMAPhysReadKB + SPMAPhysPreReadKB + SPMAPhysWriteKB)) * 100) (format 'ZZ9.9') (named "PctReadsKB")

,sum(SPMAPhysReads) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9') (named "AvgPosReadSec")
,sum(SPMAPhysPreReads) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9') (named "AvgPreReadSec")
,sum(SPMAPhysWrites) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9') (named "AvgWriteSec")

,sum(SPMAPhysReads + SPMAPhysPreReads + SPMAPhysWrites) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9') (named "AvgIOPsSecNode")
,max(SPMAPhysReads + SPMAPhysPreReads + SPMAPhysWrites) / RSSInterval (format 'ZZ,ZZ9.9') (named "MaxIOPsSecNode")
,sum(SPMAPhysReadKB + SPMAPhysPreReadKB + SPMAPhysWriteKB) / 1024.0 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9') (named "AvgMBSecNode")
,max(SPMAPhysReadKB + SPMAPhysPreReadKB + SPMAPhysWriteKB) / 1024.0 / RSSInterval (format 'ZZZ,ZZ9.9') (named "MaxMBSecNode")
,sum(SPMAPhysReadKB + SPMAPhysPreReadKB) / 1024.0 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9') (named "AvgReadMBSecNode")
,sum(SPMAPhysWriteKB) / 1024.0 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9') (named "AvgWriteMBSecNode")

,sum(SPMAPhysReadKB + SPMAPhysPreReadKB + SPMAPhysWriteKB) / 1024.0 / RSSInterval (format 'Z,ZZZ,ZZ9.9') (named "TtlMBSecGen")
,sum(SPMAPhysReadKB + SPMAPhysPreReadKB) / 1024.0 / RSSInterval (format 'Z,ZZZ,ZZ9.9') (named "TtlReadMBSecGen")
,sum(SPMAPhysWriteKB) / 1024.0 / RSSInterval (format 'Z,ZZZ,ZZ9.9') (named "TtlWriteMBSecGen")

,sum(SPMAPhysReads) / RSSInterval (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "TtlPosReadSecGen")
,sum(SPMAPhysPreReads) / RSSInterval (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "TtlPreReadSecGen")
,sum(SPMAPhysWrites) / RSSInterval (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "TtlWriteSecGen")

,zeroifnull( TtlReadMBSecGen / nullifzero(TtlPosReadSecGen + TtlPreReadSecGen) * 1024.0 ) (format 'Z,ZZ9.9') (named "KBRead")
,zeroifnull( TtlWriteMBSecGen / nullifzero(TtlWriteSecGen) * 1024.0 ) (format 'Z,ZZ9.9')(named "KBWrite")

/* SVPR Cache Effectiveness */

,zeroifnull(CASE
WHEN TtlPhyPermReadMBSecNode_SVPR > LogPermReadMBSecNode_SVPR THEN 0
ELSE (LogPermReadMBSecNode_SVPR - TtlPhyPermReadMBSecNode_SVPR)/ nullifzero(LogPermReadMBSecNode_SVPR) * 100
END) (FORMAT 'ZZ9.9', named "PermCacheEffKB")
,zeroifnull(CASE
WHEN TtlPhySpoolReadMBSecNode_SVPR > LogSpoolReadMBSecNode_SVPR THEN 0
ELSE (LogSpoolReadMBSecNode_SVPR - TtlPhySpoolReadMBSecNode_SVPR)/ nullifzero(LogSpoolReadMBSecNode_SVPR) * 100
END) (FORMAT 'ZZ9.9', named "SpoolCacheEffKB")
,zeroifnull(CASE
WHEN TtlPhyReadMBSecNode_SVPR > TtlLogReadMBSecNode_SVPR THEN 0
ELSE (TtlLogReadMBSecNode_SVPR - TtlPhyReadMBSecNode_SVPR)/ nullifzero(TtlLogReadMBSecNode_SVPR) * 100
END) (FORMAT 'ZZ9.9', named "TotalCacheEffKB")

,zeroifnull( (LogPermReadSecNode_SVPR-TtlPhyPermReadsSecNode_SVPR)
/ nullifzero(LogPermReadSecNode_SVPR) * 100) (FORMAT 'ZZ9.9', named "PermCacheEffCnt")
,zeroifnull( (LogSpoolReadSecNode_SVPR-TtlPhySpoolReadsSecNode_SVPR)
/ nullifzero(LogSpoolReadSecNode_SVPR) * 100) (FORMAT 'ZZ9.9', named "SpoolCacheEffCnt")

,zeroifnull( (LogPermDBSecNode_SVPR-PhyPermDBSecNode_SVPR)
/ nullifzero(LogPermDBSecNode_SVPR) * 100) (FORMAT 'ZZ9.9', named "PermDBCacheEffCnt")
,zeroifnull( (LogPermCISecNode_SVPR-PhyPermCISecNode_SVPR)
/ nullifzero(LogPermCISecNode_SVPR) * 100) (FORMAT 'ZZ9.9', named "PermCICacheEffCnt")

,zeroifnull( (LogSpoolDBSecNode_SVPR-PhySpoolDBSecNode_SVPR)
/ nullifzero(LogSpoolDBSecNode_SVPR) * 100) (FORMAT 'ZZ9.9', named "SpoolDBCacheEffCnt")
,zeroifnull( (LogSpoolCISecNode_SVPR-PhySpoolCISecNode_SVPR)
/ nullifzero(LogSpoolCISecNode_SVPR) * 100) (FORMAT 'ZZ9.9', named "SpoolCICacheEffCnt")

/* SVPR I/O Metrics */

,sum(LogPermDBRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "LogPermDBSecNode_SVPR")
,sum(LogPermCIRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "LogPermCISecNode_SVPR")
,sum(LogSpoolDBRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "LogSpoolDBSecNode_SVPR")
,sum(LogSpoolCIRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "LogSpoolCISecNode_SVPR")

,sum(PhySpoolDBRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "PhySpoolDBSecNode_SVPR")
,sum(PhySpoolCIRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "PhySpoolCISecNode_SVPR")
,sum(PhyPermDBRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "PhyPermDBSecNode_SVPR")
,sum(PhyPermCIRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "PhyPermCISecNode_SVPR")

,sum(LogPermRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "LogPermReadSecNode_SVPR")
,sum(LogSpoolRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "LogSpoolReadSecNode_SVPR")
,sum(LogPermReadKB) / 1024 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9')(named "LogPermReadMBSecNode_SVPR")
,sum(LogSpoolReadKB) / 1024 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9')(named "LogSpoolReadMBSecNode_SVPR")

,sum(PhyPermReadKB) / 1024 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9')(named "PhyPermPosReadMBSecNode_SVPR")
,sum(PhyPermPreReadKB) / 1024 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9')(named "PhyPermPreReadMBSecNode_SVPR")
,sum(PhySpoolReadKB) / 1024 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9')(named "PhySpoolPosReadMBSecNode_SVPR")
,sum(PhySpoolPreReadKB) / 1024 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9')(named "PhySpoolPreReadMBSecNode_SVPR")

,sum(PhyPermRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "PhyPermPosReadSecNode_SVPR")
,sum(PhyPermPreRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "PhyPermPreReadSecNode_SVPR")
,sum(PhySpoolRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "PhySpoolPosReadSecNode_SVPR")
,sum(PhySpoolPreRead) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "PhySpoolPreReadSecNode_SVPR")

,sum(PhyPermWrite) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "PhyPermWriteSecNode_SVPR")
,sum(PhySpoolWrite) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "PhySpoolWriteSecNode_SVPR")
,sum(PhyPermWriteKB) / 1024.0 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9')(named "PhyPermWriteMBSecNode_SVPR")
,sum(PhySpoolWriteKB) / 1024.0 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9')(named "PhySpoolWriteMBSecNode_SVPR")

,PhyPermPosReadMBSecNode_SVPR + PhyPermPreReadMBSecNode_SVPR (format 'ZZZ,ZZ9.9')(named "TtlPhyPermReadMBSecNode_SVPR")
,PhySpoolPosReadMBSecNode_SVPR + PhySpoolPreReadMBSecNode_SVPR (format 'ZZZ,ZZ9.9')(named "TtlPhySpoolReadMBSecNode_SVPR")
,PhyPermWriteMBSecNode_SVPR + PermAgedWriteMBSecNode_SVPR (format 'ZZZ,ZZ9.9')(named "TtlPhyPermWriteMBSecNode_SVPR")
,PhySpoolWriteMBSecNode_SVPR + SpoolAgedWriteMBSecNode_SVPR (format 'ZZZ,ZZ9.9')(named "TtlPhySpoolWriteMBSecNode_SVPR")

,PhyPermPosReadSecNode_SVPR + PhyPermPreReadSecNode_SVPR (format 'ZZ,ZZ9.9')(named "TtlPhyPermReadsSecNode_SVPR")
,PhySpoolPosReadSecNode_SVPR + PhySpoolPreReadSecNode_SVPR (format 'ZZ,ZZ9.9')(named "TtlPhySpoolReadsSecNode_SVPR")
,PhyPermWriteSecNode_SVPR + PhySpoolWriteSecNode_SVPR (format 'ZZ,ZZ9.9')(named "TtlPhyWriteSecNode_SVPR")
,PhyPermWriteMBSecNode_SVPR + PhySpoolWriteMBSecNode_SVPR (format 'ZZ,ZZ9.9')(named "TtlPhyWriteMBSecNode_SVPR")

,LogPermReadMBSecNode_SVPR + LogSpoolReadMBSecNode_SVPR (format 'ZZZ,ZZ9.9')(named "TtlLogReadMBSecNode_SVPR")
,TtlPhyPermReadMBSecNode_SVPR + TtlPhySpoolReadMBSecNode_SVPR (format 'ZZZ,ZZ9.9')(format 'ZZZ,ZZ9.9')(named "TtlPhyReadMBSecNode_SVPR")

/* SVPR extended perm db caching information */

,sum(FCRRequests) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "CylReadRequestsSecNode_SVPR")
,sum(SuccessfulFCRs) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "CylReadSecNode_SVPR")
,sum(FCRBlocksRead) / NumNodes / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "CylReadBlocksSecNode_SVPR")
,sum(FCRDeniedThresh) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9') (named "CylReadDenThrSecNode_SVPR")
,sum(FCRDeniedCache)  / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "CylReadDenCacheSecNode_SVPR")

,sum(PermDirtyRelease) / NumNodes / RSSInterval (named "PermDirtyRelSecNode_SVPR")
,sum(PermCleanRelease) / NumNodes / RSSInterval (named "PermCleanRelSecNode_SVPR")
,sum(PermDirtyReleaseKB) / 1024.0 / NumNodes / RSSInterval(named "PermDirtyRelMBSecNode_SVPR")
,sum(PermCleanReleaseKB) / 1024.0 / NumNodes / RSSInterval(named "PermCleanRelMBSecNode_SVPR")
,sum(PermDirtyAgedWriteKB) / 1024.0 / NumNodes / RSSInterval(named "PermAgedWriteMBSecNode_SVPR")

,sum(SpoolDirtyRelease) / NumNodes / RSSInterval (named "SpoolDirtyRelSecNode_SVPR")
,sum(SpoolCleanRelease) / NumNodes / RSSInterval (named "SpoolCleanRelSecNode_SVPR")
,sum(SpoolDirtyReleaseKB) / 1024.0 / NumNodes / RSSInterval(named "SpoolDirtyRelMBSecNode_SVPR")
,sum(SpoolCleanReleaseKB) / 1024.0 / NumNodes / RSSInterval(named "SpoolCleanRelMBSecNode_SVPR")
,sum(SpoolDirtyAgedWriteKB) / 1024.0 / NumNodes / RSSInterval(named "SpoolAgedWriteMBSecNode_SVPR")

,sum(WALTJWriteKB)  / 1024.0 / NumNodes / RSSInterval (named "WALTJWriteMBSecNode_SVPR")
,sum(WALTJDirtyReleaseKB)  / 1024.0 / NumNodes / RSSInterval (named "WALTJDirtyRelMBSecNode_SVPR")
,sum(PhysWALTJReadKB) / 1024.0 / NumNodes / RSSInterval (named "PhysWALTJReadMBSecNode_SVPR")

/* SPMA Physical Bynet */

,sum(PtPReads) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "AvgPtPReadsSec")
,max(PtPReads) / RSSInterval (format 'ZZ,ZZ9.9')(named "MaxPtPReadsSec")
,sum(PtPWrites) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "AvgPtPWritesSec")
,max(PtPWrites) / RSSInterval (format 'ZZ,ZZ9.9')(named "MaxPtPWritesSec")

,sum(PtPReadKB) / 1024 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9')(named "AvgPtPReadMBSec")
,max(PtPReadKB) / 1024 / RSSInterval (format 'ZZZ,ZZ9.9')(named "MaxPtPReadMBSec")
,sum(PtPWriteKB) / 1024 / NumNodes / RSSInterval (format 'ZZZ,ZZ9.9')(named "AvgPtPWriteMBSec")
,max(PtPWriteKB) / 1024 / RSSInterval (format 'ZZZ,ZZ9.9')(named "MaxPtPWriteMBSec")

,sum(BrdReads) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "AvgBrdReadsSec")
,max(BrdReads) / RSSInterval (format 'ZZ,ZZ9.9')(named "MaxBrdReadsSec")
,sum(BrdWrites) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "AvgBrdWritesSec")
,max(BrdWrites) / RSSInterval (format 'ZZ,ZZ9.9')(named "MaxBrdWritesSec")

,sum(BrdReadKB) / 1024 / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "AvgBrdReadMBSec")
,max(BrdReadKB) / 1024 / RSSInterval (format 'ZZZ,ZZ9.9')(named "MaxBrdReadMBSec")
,sum(BrdWriteKB) / 1024 / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "AvgBrdWriteMBSec")
,max(BrdWriteKB) / 1024 / RSSInterval (format 'ZZZ,ZZ9.9')(named "MaxBrdWriteMBSec")

/* memory and swapping */

,sum(MemFreeKB) / NumNodes (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "AvgNodeMemFreeKB")
,min(MinMemFreeKB) (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "MinMemFreeKB")
,max(MaxMemFreeKB) (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "MaxMemFreeKB")

,sum(MemCtxtPageReads) / NumNodes / RSSInterval (format 'Z,ZZ9.9')(named "AvgPgSwapInSec")
,max(MemCtxtPageReads) / RSSInterval (format 'Z,ZZ9.9')(named "MaxPgSwapInSec")
,sum(MemCtxtPageWrites) / NumNodes / RSSInterval (format 'Z,ZZ9.9')(named "AvgPgSwapOutSec")
,max(MemCtxtPageWrites) / RSSInterval (format 'Z,ZZ9.9')(named "MaxPgSwapOutSec")

/* TVS */

,sum(HDDReadKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgHDDReadMBSecNode_SPDSK")
,max(HDDReadKB) / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxHDDReadMBSecNode_SPDSK")
,sum(HDDWriteKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgHDDWriteMBSecNode_SPDSK")
,max(HDDWriteKB) / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxHDDWriteMBSecNode_SPDSK")
,sum(HDDReads) / NumNodes / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "AvgHDDReadsSecNode_SPDSK")
,max(HDDReads) / RSSInterval   (format 'ZZ,ZZZ,ZZ9.9') (named "MaxHDDReadsSecNode_SPDSK")
,sum(HDDWrites) / NumNodes / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "AvgHDDWritesSecNode_SPDSK")
,max(HDDWrites) / RSSInterval   (format 'ZZ,ZZZ,ZZ9.9') (named "MaxHDDWritesSecNode_SPDSK")
,zeroifnull(sum(HDDTotReadResp / nullifzero(HDDReads)) * 10) (format 'Z,ZZ9.9') (named "AvgHDDReadResp")
,max(HDDReadRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxHDDReadResp")
,zeroifnull(sum(HDDTotWriteResp / nullifzero(HDDWrites)) * 10) (format 'Z,ZZ9.9') (named "AvgHDDWriteResp")
,max(HDDWriteRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxHDDWriteResp")

,sum(SSDReadKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgSSDReadMBSecNode_SPDSK")
,max(SSDReadKB) / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxSSDReadMBSecNode_SPDSK")
,sum(SSDWriteKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgSSDWriteMBSecNode_SPDSK")
,max(SSDWriteKB) / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxSSDWriteMBSecNode_SPDSK")
,sum(SSDReads) / NumNodes / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "AvgSSDReadsSecNode_SPDSK")
,max(SSDReads) / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "MaxSSDReadsSecNode_SPDSK")
,sum(SSDWrites) / NumNodes / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "AvgSSDWritesSecNode_SPDSK")
,max(SSDWrites) / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "MaxSSDWritesSecNode_SPDSK")
,zeroifnull(sum(SSDTotReadResp / nullifzero(SSDReads)) * 10) (format 'Z,ZZ9.9') (named "AvgSSDReadResp")
,max(SSDReadRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxSSDReadResp")
,zeroifnull(sum(SSDTotWriteResp / nullifzero(SSDWrites)) * 10) (format 'Z,ZZ9.9') (named "AvgSSDWriteResp")
,max(SSDWriteRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxSSDWriteResp")

,sum(WISSDReadKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgWISSDReadMBSecNode_SPDSK")
,max(WISSDReadKB) / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxWISSDReadMBSecNode_SPDSK")
,sum(WISSDWriteKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgWISSDWriteMBSecNode_SPDSK")
,max(WISSDWriteKB) / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxWISSDWriteMBSecNode_SPDSK")
,sum(WISSDReads) / NumNodes / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "AvgWISSDReadsSecNode_SPDSK")
,max(WISSDReads) / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "MaxWISSDReadsSecNode_SPDSK")
,sum(WISSDWrites) / NumNodes / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "AvgWISSDWritesSecNode_SPDSK")
,max(WISSDWrites) / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "MaxWISSDWritesSecNode_SPDSK")
,zeroifnull(sum(WISSDTotReadResp / nullifzero(WISSDReads)) * 10) (format 'Z,ZZ9.9') (named "AvgWISSDReadResp")
,max(WISSDReadRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxWISSDReadResp")
,zeroifnull(sum(WISSDTotWriteResp / nullifzero(WISSDWrites)) * 10) (format 'Z,ZZ9.9') (named "AvgWISSDWriteResp")
,max(WISSDWriteRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxWISSDWriteResp")

,sum(RISSDReadKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgRISSDReadMBSecNode_SPDSK")
,max(RISSDReadKB) / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxRISSDReadMBSecNode_SPDSK")
,sum(RISSDWriteKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgRISSDWriteMBSecNode_SPDSK")
,max(RISSDWriteKB) / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxRISSDWriteMBSecNode_SPDSK")
,sum(RISSDReads) / NumNodes / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "AvgRISSDReadsSecNode_SPDSK")
,max(RISSDReads) / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "MaxRISSDReadsSecNode_SPDSK")
,sum(RISSDWrites) / NumNodes / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "AvgRISSDWritesSecNode_SPDSK")
,max(RISSDWrites) / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "MaxRISSDWritesSecNode_SPDSK")
,zeroifnull(sum(RISSDTotReadResp / nullifzero(RISSDReads)) * 10) (format 'Z,ZZ9.9') (named "AvgRISSDReadResp")
,max(RISSDReadRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxRISSDReadResp")
,zeroifnull(sum(RISSDTotWriteResp / nullifzero(RISSDWrites)) * 10) (format 'Z,ZZ9.9') (named "AvgRISSDWriteResp")
,max(RISSDWriteRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxRISSDWriteResp")

/* Logical CPU */

,sum(TotalPECPUBusy) / NumNodes / CPUs / RSSInterval (format 'ZZ9.9') (named "AvgPECPUBusy")
,max(TotalPECPUBusy) / CPUs / RSSInterval (format 'ZZ9.9') (named "MaxPECPUBusy")
,sum(TotalGTWCPUBusy) / NumNodes / CPUs / RSSInterval (format 'ZZ9.9') (named "AvgGTWCPUBusy")
,max(TotalGTWCPUBusy) / CPUs / RSSInterval (format 'ZZ9.9') (named "MaxGTWCPUBusy")
,sum(TotalAMPCPUBusy) / NumNodes / CPUs / RSSInterval (format 'ZZ9.9') (named "AvgAMPCPUBusy")
,max(TotalAMPCPUBusy) / CPUs / RSSInterval (format 'ZZ9.9') (named "MaxAMPCPUBusy")
,sum(TotalGTW_PECPUBusy) / NumNodes / CPUs / RSSInterval (format 'ZZ9.9') (named "AvgGTW_PECPUBusy")
,max(TotalGTW_PECPUBusy) / CPUs / RSSInterval (format 'ZZ9.9') (named "MaxGTW_PECPUBusy")

/* VH Cache */

,sum(VHAgedOut) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "AvgVHAgedOut_SVPR")
,sum(VHAgedOutKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZ,ZZ9.9')(named "AvgVHAgedOutMBSecNode_SVPR")
,sum(VHAcqs) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "AvgLogVHReads_SVPR")
,sum(VHAcqKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZ,ZZ9.9')(named "AvgLogVHReadMBSecNode_SVPR")
,sum(VHAcqReads) / NumNodes / RSSInterval (format 'ZZ,ZZ9.9')(named "AvgPhysVHReads_SVPR")
,sum(VHAcqReadKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZ,ZZ9.9')(named "AvgPhysVHReadMBSecNode_SVPR")

/* Compression */

,sum(PreCompMB) / NumNodes / RSSInterval (named "PreCompMBSecNode_SVPR")
,sum(PostCompMB) / NumNodes / RSSInterval (named "PostCompMBSecNode_SVPR")
,sum(PreUnCompMB) / NumNodes / RSSInterval (named "PreUnCompMBSecNode_SVPR")
,sum(PostUnCompMB) / NumNodes / RSSInterval (named "PostUnCompMBSecNode_SVPR")
,sum(CompDBs) / NumNodes / RSSInterval (named "CompDBsSecNode_SVPR")
,sum(UnCompDBs) / NumNodes / RSSInterval (named "UnCompDBsSecNode_SVPR")

,sum(CompCPUMS) (named "COMPCPU")
,sum(UnCompCPUMS) (named "UNCOMPCPU")

,sum(CompCPUMS) / 10 / NumNodes / CPUs / RSSInterval  (named "PctCPUComp")
,sum(UnCompCPUMS) / 10 / NumNodes / CPUs / RSSInterval  (named "PctCPUUnComp")

,zeroifnull(PreCompMBSecNode_SVPR / nullifzero(PostCompMBSecNode_SVPR)) (named "CompRatioComp_SVPR")
,zeroifnull(PostUnCompMBSecNode_SVPR / nullifzero(PreUnCompMBSecNode_SVPR)) (named "CompRatioUnComp_SVPR")

/* comp1 & 2 estimates only valid when BLC already being used
	estimate using 25 ms/mb compress, 3.5 ms/mb uncompress */

,zeroifnull(PctCPUComp) / 100 * NumNodes * CPUs / 2 / (PMCOD / 100) (named "TtlTCPUComp_Est1")
,zeroifnull(PctCPUUnComp) / 100 * NumNodes  * CPUs / 2 / (PMCOD / 100)   (named "TtlTCPUUnComp_Est1")

,zeroifnull(PreCompMBSecNode_SVPR) * NumNodes * 0.025 / 2  (named "TtlTCPUComp_Est2")
,zeroifnull(PostUnCompMBSecNode_SVPR) * NumNodes * 0.0035 / 2  (named "TtlTCPUUnComp_Est2")

,PhyPermWriteMBSecNode_SVPR * NumNodes * 0.025 / 2  (named "TtlTCPUComp_Est3")
,LogPermReadMBSecNode_SVPR * NumNodes * 0.0035 / 2  (named "TtlTCPUUnComp_Est3")

,zeroifnull(sum(CompCPUMS) / NumNodes / RSSInterval / nullifzero(PreCompMBSecNode_SVPR))  (named "CPUMSMBComp")
,zeroifnull(sum(UnCompCPUMS) / NumNodes / RSSInterval / nullifzero(PostUnCompMBSecNode_SVPR))  (named "CPUMSMBUnComp")

/* NCS Node sizing */

,AvgGTW_PECPUBusy / 100 * NumNodes * CPUs / 2 / (PMCOD / 100) / 100 (named "TotalTCPUForNCSNodes")
,AvgGTW_PECPUBusy / 100 * NumNodes * CPUs / 2 / (PMCOD / 100) / 100 (named "AvgTCPUForNCSNode")
,MaxGTW_PECPUBusy / 100 * NumNodes * CPUs / 2 / (PMCOD / 100) / 100 (named "MaxTCPUForNCSNode")

,sum(NtwReadKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgNtwReadMBSecNode")
,max(NtwReadKB) / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxNtwReadMBSecNode")

,sum(NtwWriteKB) / NumNodes / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgNtwWriteMBSecNode")
,max(NtwWriteKB) / RSSInterval / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxNtwWriteMBSecNode")

,sum(NtwReadKB) / RSSInterval / 1024.0 (format 'Z,ZZZ,ZZ9.9') (named "TotalNtwReadMBSecNode")
,sum(NtwWriteKB) / RSSInterval / 1024.0 (format 'Z,ZZZ,ZZ9.9') (named "TotalNtwWriteMBSecNode")

from dbc.dbcinfo info,
(
sel
sum(CurrentPerm) (named "SumCurrPerm")
,sum(MaxPerm) (named "SumMaxPerm")
,sum(PeakSpool) (named "SumPeakSpool")
,sum(PeakTemp) (named "SumPeakTemp")
FROM DBC.DiskSpaceV

) diskspacev_dt,
(

sel
thedate (format 'yyyy-mm-dd')(named "LogDate")
,thedate (format 'EEE') (named "LogDay")
,cast(thetime as int) / 10 * 10      (format '99:99:99') (named "LogTime")
,Secs (named "SPMAInterval")
,NodeID
,NodeType
,vproc1
,NCpus
,MemSize / 1024.0 (Named "MemSizeGB")
,PM_COD_CPU / 10.0 (Named "PM_COD")
,WM_COD_CPU / 10.0 (Named "WM_COD")
,CASE when PM_COD_IO > WM_COD_IO then WM_COD_IO ELSE PM_COD_IO END (Named "IO_COD")
,CASE WHEN COALESCE (TDEnabledCPUs,0) = 0 OR NCPUs = TDEnabledCPUs THEN NCPUs ELSE TDEnabledCPUs END (Named "TDEnabledCPUs")

/* CPU */

,sum(CPUUExec+CPUUServ) (named "CPUUtil")
,zeroifnull(sum(CPUUServ) / nullifzero(CPUUtil) * 100) (named "OSPctCPU")
,sum(CPUUServ) (named "ServCPUUtil")
,sum(CPUIoWait) (named "IOWaitCPUUtil")
,avg(ProcReady) (named "RunQSz")
,max(ProcReadyMax) (named "MaxRunQSz")

/* Physical I/O */

,sum(FileAcqReads) (named "SPMAPhysReads")
,sum(FilePreReads) (named "SPMAPhysPreReads")
,sum(FileWrites) (named "SPMAPhysWrites")
,sum(FileAcqReadKB) (named "SPMAPhysReadKB")
,sum(FilePreReadKB) (named "SPMAPhysPreReadKB")
,sum(FileWriteKB) (named "SPMAPhysWriteKB")

/* Physical Bynet Traffic */

,sum(NetMsgPtPReads) (named "PtPReads")
,sum(NetMsgPtPWrites) (named "PtPWrites")
,sum(NetMsgPtPReadKB) (named "PtPReadKB")
,sum(NetMsgPtPWriteKB) (named "PtPWriteKB")
,sum(NetMsgBrdReads) (named "BrdReads")
,sum(NetMsgBrdWrites) (named "BrdWrites")
,sum(NetMsgBrdReadKB) (named "BrdReadKB")
,sum(NetMsgBrdWriteKB) (named "BrdWriteKB")

/* memory and swapping */

,sum(MemFreeKB) (named "MemFreeKB")
,min(MemFreeKB) (named "MinMemFreeKB")
,max(MemFreeKB) (named "MaxMemFreeKB")

,sum(MemCtxtPageReads) (named "MemCtxtPageReads")
,sum(MemCtxtPageWrites) (named "MemCtxtPageWrites")

/* VH Cache */

,sum(VHCacheKB) (named "VHCacheKB")
,max(VHCacheKB) (named "MaxVHCacheKB")

/* ntw traffic */

,sum(HostReadKB) (named "NtwReadKB")
,sum(HostWriteKB) (named "NtwWriteKB")

from PDCRINFO.ResUsageSpma_hst
WHERE ( ( THEDATE = {{ startdate | default ('date-45') }} AND THETIME >= {{ starttime | default ('0') }} ) OR
( THEDATE > {{ startdate | default ('date-45') }} ) )
AND
( ( THEDATE = {{ enddate | default ('date-1')  }} AND THETIME <= {{ endtime | default ('240000') }} ) OR
( THEDATE < {{ enddate | default ('date-1')  }} ) )
group by 1,2,3,4,5,6,7,8,9,10,11,12,13

) spma_dt left join

(
sel
thedate (format 'yyyy-mm-dd')(named "LogDate")
,cast(thetime as int) / 10 * 10      (format '99:99:99') (named "LogTime")
,Secs (named "SVPRInterval")
,NodeID

,sum(FilePDbAcqs)(named "LogPermDBRead")
,sum(FilePCiAcqs)(named "LogPermCIRead")
,LogPermDBRead+LogPermCIRead (named "LogPermRead")

,sum(FileSDbAcqs)(named "LogSpoolDBRead")
,sum(FileSCiAcqs)(named "LogSpoolCIRead")
,LogSpoolDBRead+LogSpoolCIRead (named "LogSpoolRead")

,sum(FilePDbAcqKB + FilePCiAcqKB)(named "LogPermReadKB")
,sum(FileSDbAcqKB + FileSCiAcqKB)(named "LogSpoolReadKB")

,sum(FilePDbAcqReads) (named "PhyPermDBRead")
,sum(FilePCiAcqReads) (named "PhyPermCIRead")
,PhyPermDBRead+PhyPermCIRead (named "PhyPermRead")

,sum(FilePDbPreReads + FilePCiPreReads) (named "PhyPermPreRead")

,sum(FileSDbAcqReads) (named "PhySpoolDBRead")
,sum(FileSCiAcqReads) (named "PhySpoolCIRead")
,PhySpoolDBRead+PhySpoolCIRead (named "PhySpoolRead")

,sum(FileSDbPreReads + FileSCiPreReads) (named "PhySpoolPreRead")

,sum(FilePDbAcqReadKB + FilePCiAcqReadKB) (named "PhyPermReadKB")
,sum(FilePDbPreReadKB + FilePCiPreReadKB) (named "PhyPermPreReadKB")
,sum(FileSDbAcqReadKB + FileSCiAcqReadKB) (named "PhySpoolReadKB")
,sum(FileSDbPreReadKB + FileSCiPreReadKB) (named "PhySpoolPreReadKB")

,sum(FilePDbFWrites + FilePCiFWrites) (named "PhyPermWrite")
,sum(FileSDbFWrites + FileSCiFWrites) (named "PhySpoolWrite")
,sum(FilePDbFWriteKB + FilePCiFWriteKB) (named "PhyPermWriteKB")
,sum(FileSDbFWriteKB + FileSCiFWriteKB) (named "PhySpoolWriteKB")

/* extra perm db svpr for caching & WAl/TJ I/O */

,sum(FilePDbDyRRels) (named "PermDirtyRelease")
,sum(FilePDbCnRRels) (named "PermCleanRelease")
,sum(FilePDbDyAWrites) (named "PermDirtyAgedWrite")

,sum(FilePDbDyRRelKB) (named "PermDirtyReleaseKB")
,sum(FilePDbCnRRelKB) (named "PermCleanReleaseKB")
,sum(FilePDbDyAWriteKB) (named "PermDirtyAgedWriteKB")

,sum(FileSDbDyRRels) (named "SpoolDirtyRelease")
,sum(FileSDbCnRRels) (named "SpoolCleanRelease")
,sum(FileSDbDyRRelKB) (named "SpoolDirtyReleaseKB")
,sum(FileSDbCnRRelKB) (named "SpoolCleanReleaseKB")
,sum(FileSDbDyAWriteKB) (named "SpoolDirtyAgedWriteKB")

,sum(FileTJtFWriteKB) (named "WALTJWriteKB")
,sum(FileTJtDyAWriteKB)(named "WALTJDirtyReleaseKB")
,sum(FileTJtPreReadKB+FileTJtAcqReadKB)(named "PhysWALTJReadKB")

/* BLC */

,sum(FilePreCompMB) (named "PreCompMB")
,sum(FilePostCompMB) (named "PostCompMB")
,sum(FilePreUnCompMB) (named "PreUnCompMB")
,sum(FilePostUnCompMB) (named "PostUnCompMB")
,sum(FileCompDBs) (named "CompDBs")
,sum(FileUnCompDBs) (named "UnCompDBs")
,sum(FileCompCPU) / 1000 (named "CompCPUMS")
,sum(FileUnCompCPU) / 1000 (named "UnCompCPUMS")

/* cyl read stuff */

,sum(FileFcrRequests) (named "FCRRequests")
,sum(FileFcrRequests-FileFcrDeniedUser-FileFcrDeniedKern) (named "SuccessfulFCRs")
,sum(FileFcrBlocksRead) (named "FCRBlocksRead")
,sum(FileFcrDeniedThreshKern+FileFcrDeniedThreshUser) (named "FCRDeniedThresh")
,sum(FileFcrDeniedCache) (named "FCRDeniedCache")

/* Logical CPU stuff */

,sum(CASE WHEN VprType like 'PE%' THEN CPUUExecPart13 ELSE 0 END) (named "PEDispExec")
,sum(CASE WHEN VprType like 'PE%' THEN CPUUServPart13 ELSE 0 END) (named "PEDispServ")
,sum(CASE WHEN VprType like 'PE%' THEN CPUUExecPart14 ELSE 0 END) (named "PEParsExec")
,sum(CASE WHEN VprType like 'PE%' THEN CPUUServPart14 ELSE 0 END) (named "PEParsServ")
,sum(CASE WHEN VprType like 'PE%' THEN CPUUExecPart12 ELSE 0 END) (named "PESessExec")
,sum(CASE WHEN VprType like 'PE%' THEN CPUUServPart12 ELSE 0 END) (named "PESessServ")

,PEDispExec + PEDispServ + PEParsExec + PEParsServ + PESessExec + PESessServ (named "TotalPECPUBusy")

,sum(CASE WHEN VprType like 'GTW%' THEN CPUUExecPart10 ELSE 0 END) (named "GTWExec")
,sum(CASE WHEN VprType like 'GTW%' THEN CPUUServPart10 ELSE 0 END) (named "GTWServ")

,GTWExec + GTWServ (named "TotalGTWCPUBusy")

,TotalPECPUBusy + TotalGTWCPUBusy (named "TotalGTW_PECPUBusy")

,sum(CASE WHEN VprType like 'AMP%' THEN CPUUExecPart11 ELSE 0 END) (named "AMPWorkTaskExec")
,sum(CASE WHEN VprType like 'AMP%' THEN CPUUServPart11 ELSE 0 END) (named "AMPWorkTaskServ")

,AMPWorkTaskExec + AMPWorkTaskServ (named "TotalAMPCPUBusy")

/* VH cache */

,sum(VHAgedOut) (named "VHAgedOut")
,sum(VHAgedOutKB) (named "VHAgedOutKB")
,sum(VHLogicalDBRead) (named "VHAcqs")
,sum(VHLogicalDBReadKB) (named "VHAcqKB")
,sum(VHPhysicalDBRead) (named "VHAcqReads")
,sum(VHPhysicalDBReadKB) (named "VHAcqReadKB")

from PDCRINFO.ResUsageSvpr_hst
WHERE ( ( THEDATE = {{ startdate | default ('date-45') }} AND THETIME >= {{ starttime | default ('0') }} ) OR
( THEDATE > {{ startdate | default ('date-45') }} ) )
AND
( ( THEDATE = {{ enddate | default ('date-1')  }} AND THETIME <= {{ endtime | default ('240000') }} ) OR
( THEDATE < {{ enddate | default ('date-1')  }} ) )

group by 1,2,3,4

) svpr_dt
on spma_dt.LogDate = svpr_dt.LogDate
and spma_dt.LogTime = svpr_dt.LogTime
and spma_dt.nodeid = svpr_dt.nodeid
left join
(
sel
thedate (format 'yyyy-mm-dd')(named "LogDate")
,cast(thetime as int) / 10 * 10      (format '99:99:99') (named "LogTime")
,Secs (named "SPDSKInterval")
,NodeID
,sum(case when PdiskType = 'DISK' then ReadKB else 0 END) (named "HDDReadKB")
,sum(case when PdiskType = 'DISK' then WriteKB else 0 END) (named "HDDWriteKB")
,sum(case when PdiskType = 'DISK' then ReadCnt else 0 END) (named "HDDReads")
,sum(case when PdiskType = 'DISK' then WriteCnt else 0 END) (named "HDDWrites")
,sum(case when PdiskType = 'DISK' then ReadRespTot else 0 END) (named "HDDTotReadResp")
,sum(case when PdiskType = 'DISK' then WriteRespTot else 0 END) (named "HDDTotWriteResp")
,max(case when PdiskType = 'DISK' then ReadRespMax else 0 END) (named "HDDReadRespMax")
,max(case when PdiskType = 'DISK' then WriteRespMax else 0 END) (named "HDDWriteRespMax")

,sum(case when PdiskType = 'SSD' then ReadKB else 0 END) (named "SSDReadKB")
,sum(case when PdiskType = 'SSD' then WriteKB else 0 END) (named "SSDWriteKB")
,sum(case when PdiskType = 'SSD' then ReadCnt else 0 END) (named "SSDReads")
,sum(case when PdiskType = 'SSD' then WriteCnt else 0 END) (named "SSDWrites")
,sum(case when PdiskType = 'SSD' then ReadRespTot else 0 END) (named "SSDTotReadResp")
,sum(case when PdiskType = 'SSD' then WriteRespTot else 0 END) (named "SSDTotWriteResp")
,max(case when PdiskType = 'SSD' then ReadRespMax else 0 END) (named "SSDReadRespMax")
,max(case when PdiskType = 'SSD' then WriteRespMax else 0 END) (named "SSDWriteRespMax")

/* add RI/WI SSD breakdown */

,sum(case when PdiskType = 'WSSD' then ReadKB else 0 END) (named "WISSDReadKB")
,sum(case when PdiskType = 'WSSD' then WriteKB else 0 END) (named "WISSDWriteKB")
,sum(case when PdiskType = 'WSSD' then ReadCnt else 0 END) (named "WISSDReads")
,sum(case when PdiskType = 'WSSD' then WriteCnt else 0 END) (named "WISSDWrites")
,sum(case when PdiskType = 'WSSD' then ReadRespTot else 0 END) (named "WISSDTotReadResp")
,sum(case when PdiskType = 'WSSD' then WriteRespTot else 0 END) (named "WISSDTotWriteResp")
,max(case when PdiskType = 'WSSD' then ReadRespMax else 0 END) (named "WISSDReadRespMax")
,max(case when PdiskType = 'WSSD' then WriteRespMax else 0 END) (named "WISSDWriteRespMax")

,sum(case when PdiskType = 'RSSD' then ReadKB else 0 END) (named "RISSDReadKB")
,sum(case when PdiskType = 'RSSD' then WriteKB else 0 END) (named "RISSDWriteKB")
,sum(case when PdiskType = 'RSSD' then ReadCnt else 0 END) (named "RISSDReads")
,sum(case when PdiskType = 'RSSD' then WriteCnt else 0 END) (named "RISSDWrites")
,sum(case when PdiskType = 'RSSD' then ReadRespTot else 0 END) (named "RISSDTotReadResp")
,sum(case when PdiskType = 'RSSD' then WriteRespTot else 0 END) (named "RISSDTotWriteResp")
,max(case when PdiskType = 'RSSD' then ReadRespMax else 0 END) (named "RISSDReadRespMax")
,max(case when PdiskType = 'RSSD' then WriteRespMax else 0 END) (named "RISSDWriteRespMax")

from PDCRINFO.ResUsageSpdsk_hst
WHERE ( ( THEDATE = {{ startdate | default ('date-45') }} AND THETIME >= {{ starttime | default ('0') }} ) OR
( THEDATE > {{ startdate | default ('date-45') }} ) )
AND
( ( THEDATE = {{ enddate | default ('date-1')  }} AND THETIME <= {{ endtime | default ('240000') }} ) OR
( THEDATE < {{ enddate | default ('date-1')  }} ) )
group by 1,2,3,4

) spdsk_dt
on spma_dt.LogDate = spdsk_dt.LogDate
and spma_dt.LogTime = spdsk_dt.LogTime
and spma_dt.nodeid = spdsk_dt.nodeid
where  info.infokey (NOT CS) = 'VERSION' (NOT CS)
group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22
--- order by 5,14



) with data  primary index(LogDate, LogTime)  on commit preserve rows