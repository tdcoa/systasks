replace macro systemfe.gss_resusage_td14
( BEGINDATE (DATE, DEFAULT DATE)
 , ENDDATE (DATE, DEFAULT DATE)
 , BEGINTIME (INT, DEFAULT 0)
 , ENDTIME (INT, DEFAULT 240000)
 )
 AS (
 /* gss_resusage_td1400-R005 */
 sel
 'TD14v1.72' (named "Version")
 ,spma_dt.LogDate (named "LogDate")
 ,cast(spma_dt.LogDay as char(3)) (named "LogDOW")
 ,spma_dt.LogTime (named "LogTime")
 ,cast((spma_dt.LogDate || ' ' || spma_dt.LogTime) as timestamp(0)) (named "Timestamp")
 ,extract(hour from "Timestamp") (named "Hour")
 ,extract(minute from "Timestamp") (named "Minute")
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

,diskspacev_dt.SumCurrPerm (named "SumCurrPerm")
,diskspacev_dt.SumMaxPerm (named "SumMaxPerm")
,diskspacev_dt.SumPeakSpool (named "SumPeakSpool")
,diskspacev_dt.SumPeakTemp (named "SumPeakTemp")

,cast(((case
when ( NodeGen in ('6800','6800H','1800','2800','680'))  then 5.35 * CPUs
when ( NodeGen in ('6750','6750H','6750P','6750HX','6750X','675','675HDD','2750','2755','1750')) then 5 * CPUs
when ( NodeGen in ('6700','6700H','2700','1700','670H','6700HDD') and CPUs = 32) then 167.74
when ( NodeGen in ('6700','6700C','670C') and CPUs = 18) then 99.19
when ( NodeGen in ('6690','6690H','2690') and CPUs = 24) then 132.25
when ( NodeGen in ('6680','6650H','6650','5650H','5650','4650','2650','1650') and CPUs = 24) then 129.03
when ( NodeGen in ('6650C','6650','5650C','5650','560C') and CPUs = 12 ) then 68.38
when ( NodeGen in ('5600H','5600','560H','4600','2580','1600','1580') and CPUs = 16) then 86.02
when ( NodeGen in ('5600C','5600','560C') and CPUs = 8) then 45.59
when ( NodeGen in ('5550','2550','1550') and CPUs = 8) then 50.89
when ( NodeGen in ('5550','5555') and CPUs = 4) then 27.63
when ( NodeGen in ('5500H','5500','2500') and CPUs = 4) then 31.72
when ( NodeGen in ('5500C','5500') and CPUs = 2) then 16.81
when NodeGen = '5450' then 13.36
when NodeGen = '5400' then 11.72
when NodeGen in ('5380','4980') then 8.80
when NodeGen in ('5350','4950') then 6.13
when NodeGen in ('5300','4900') then 4.68
else 0
end) ) as decimal(5,2)) (named "NodeT")


/*** end grouping fields ***/

 , ( (0.005 * (TtlPosReadSecGen + TtlPreReadSecGen + 2*TtlWriteSecGen)) +
 (TtlReadMBSecGen + 2*TtlWriteMBSecGen)/150 ) / .8 (format 'ZZ,ZZ9.9')(named "D")
 ,NodeT * NumNodes * AvgCPUBusy / 100 /.8 (format 'ZZ,ZZ9.9') (Named "T")
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

/* swapping */

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
 ,max(HDDReads) / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "MaxHDDReadsSecNode_SPDSK")
 ,sum(HDDWrites) / NumNodes / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "AvgHDDWritesSecNode_SPDSK")
 ,max(HDDWrites) / RSSInterval (format 'ZZ,ZZZ,ZZ9.9') (named "MaxHDDWritesSecNode_SPDSK")
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

/* Logical CPU */

,sum(TotalPECPUBusy) / NumNodes / CPUs / RSSInterval (format 'ZZ9.9') (named "AvgPECPUBusy")
,max(TotalPECPUBusy) / CPUs / RSSInterval (format 'ZZ9.9') (named "MaxPECPUBusy")
,sum(TotalGTWCPUBusy) / NumNodes / CPUs / RSSInterval (format 'ZZ9.9') (named "AvgGTWCPUBusy")
,max(TotalGTWCPUBusy) / CPUs / RSSInterval (format 'ZZ9.9') (named "MaxGTWCPUBusy")
,sum(TotalAMPCPUBusy) / NumNodes / CPUs / RSSInterval (format 'ZZ9.9') (named "AvgAMPCPUBusy")
,max(TotalAMPCPUBusy) / CPUs / RSSInterval (format 'ZZ9.9') (named "MaxAMPCPUBusy")
,sum(TotalGTW_PECPUBusy) / NumNodes / CPUs / RSSInterval (format 'ZZ9.9') (named "AvgGTW_PECPUBusy")
,max(TotalGTW_PECPUBusy) / CPUs / RSSInterval (format 'ZZ9.9') (named "MaxGTW_PECPUBusy")
 
/* Compression */

,sum(PreCompMB) / NumNodes / RSSInterval (named "PreCompMBSecNode_SVPR")
,sum(PostCompMB) / NumNodes / RSSInterval (named "PostCompMBSecNode_SVPR")
,sum(PreUnCompMB) / NumNodes / RSSInterval (named "PreUnCompMBSecNode_SVPR")
,sum(PostUnCompMB) / NumNodes / RSSInterval (named "PostUnCompMBSecNode_SVPR")
,sum(CompDBs) / NumNodes / RSSInterval (named "CompDBsSecNode_SVPR")
,sum(UnCompDBs) / NumNodes / RSSInterval (named "UnCompDBsSecNode_SVPR")

,sum(CompCPUMS) / 10 / NumNodes / CPUs / RSSInterval  (named "PctCPUComp")
,sum(UnCompCPUMS) / 10 / NumNodes / CPUs / RSSInterval  (named "PctCPUUnComp")

,zeroifnull(PreCompMBSecNode_SVPR / nullifzero(PostCompMBSecNode_SVPR)) (named "CompRatioComp_SVPR")
,zeroifnull(PostUnCompMBSecNode_SVPR / nullifzero(PreUnCompMBSecNode_SVPR)) (named "CompRatioUnComp_SVPR")

/* comp1 & 2 estimates only valid when BLC already being used */

,zeroifnull(PctCPUComp) / 100 * NodeT * NumNodes / (PMCOD / 100) * 1.2 / 300 (named "TtlBentleyCompNodes_Est1")
,zeroifnull(PctCPUUnComp) / 100 * NodeT * NumNodes / (PMCOD / 100) * 1.2 / 300 (named "TtlBentleyUnCompNodes_Est1")

,zeroifnull(PreCompMBSecNode_SVPR) * NumNodes * 0.16 / (PMCOD / 100) * 1.2 / 300 (named "TtlBentleyCompNodes_Est2") 
,zeroifnull(PostUnCompMBSecNode_SVPR) * NumNodes * 0.021 / (PMCOD / 100) * 1.2 / 300 (named "TtlBentleyUnCompNodes_Est2") 

/* others go off of reads/writes & assumes 3x compression */

,PhyPermWriteMBSecNode_SVPR * NumNodes * 0.20 / (PMCOD / 100) * 1.2 * 3 / 300 (named "TtlBentleyCompNodes_Est3") 
,LogPermReadMBSecNode_SVPR * NumNodes * 0.026 / (PMCOD / 100) * 1.2 * 3 / 300 (named "TtlBentleyUnCompNodes_Est3") 

,TtlPhyPermWriteMBSecNode_SVPR * NumNodes * 0.20 / (PMCOD / 100) * 1.2 * 3 / 300 (named "TtlBentleyCompNodes_Est4")

,(AvgWriteMBSecNode - TtlPhySpoolWriteMBSecNode_SVPR) * NumNodes * 0.20 / (PMCOD / 100) * 1.2 * 3 / 300 (named "TtlBentleyCompNodes_Est5")

,zeroifnull(sum(CompCPUMS) / NumNodes / RSSInterval / nullifzero(PreCompMBSecNode_SVPR))  (named "CPUMSMBComp")
,zeroifnull(sum(UnCompCPUMS) / NumNodes / RSSInterval / nullifzero(PostUnCompMBSecNode_SVPR))  (named "CPUMSMBUnComp")

,case when NodeGen in ('2690','2700','2750','2800') then TtlBentleyCompNodes_Est2 else TtlBentleyCompNodes_Est3 end (named "TtlBentleyCompNodes_Est")
,case when NodeGen in ('2690','2700','2750','2800') then TtlBentleyUnCompNodes_Est2 else TtlBentleyUnCompNodes_Est3 end (named "TtlBentleyUnCompNodes_Est")

/* for reference -- legacy compression cost estimates */

,TtlPhyPermWriteMBSecNode_SVPR * NumNodes * .64 (named "OrigCompEst") 
,LogPermReadMBSecNode_SVPR * NumNodes * .064 (named "OrigUnCompEst")

/* NCS Node sizing */

,AvgGTW_PECPUBusy / 100 * NodeT * NumNodes / (PMCOD / 100) * 1.2 / 100 / 160 (named "TtlBentleyNCSNodes") -- 6800C -like NCS node, 6700C is 2x this.
,AvgGTW_PECPUBusy / 100 * NodeT / (PMCOD / 100) * 1.2 / 100 (named "AvgGTW_PENCSNode") 
,MaxGTW_PECPUBusy / 100 * NodeT / (PMCOD / 100) * 1.2 / 100 (named "MaxGTW_PENCSNode")

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
 ,cast(thetime as int) / 1000 * 1000 (format '99:99:99') (named "LogTime")
 ,600 (named "SPMAInterval")
 ,NodeID
 ,NodeType
 ,vproc1
 ,NCpus
 ,MemSize / 1024.0 (Named "MemSizeGB")
,CODFactor / 10.0 (Named "PM_COD")
,Spare11 / 10.0 (Named "WM_COD")
,CASE when SpareInt > Spare01 then Spare01 ELSE SpareInt END (Named "IO_COD")

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
 ,sum(Spare00) (named "SPMAPhysPreReadKB")
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

/* swapping */

,sum(MemCtxtPageReads) (named "MemCtxtPageReads")
 ,sum(MemCtxtPageWrites) (named "MemCtxtPageWrites")

/* ntw traffic */

,sum(HostReadKB) (named "NtwReadKB")
,sum(HostWriteKB) (named "NtwWriteKB")

from dbc.resusagespma
 WHERE ( ( THEDATE = :BEGINDATE AND THETIME >= :BEGINTIME ) OR
 ( THEDATE > :BEGINDATE ) )
 AND
 ( ( THEDATE = :ENDDATE AND THETIME <= :ENDTIME ) OR
 ( THEDATE < :ENDDATE ) )
 group by 1,2,3,4,5,6,7,8,9,10,11,12

) spma_dt left join

(
 sel
 thedate (format 'yyyy-mm-dd')(named "LogDate")
 ,cast(thetime as int) / 1000 * 1000 (format '99:99:99') (named "LogTime")
 ,600 (named "SVPRInterval")
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

from dbc.resusagesvpr
 WHERE ( ( THEDATE = :BEGINDATE AND THETIME >= :BEGINTIME ) OR
 ( THEDATE > :BEGINDATE ) )
 AND
 ( ( THEDATE = :ENDDATE AND THETIME <= :ENDTIME ) OR
 ( THEDATE < :ENDDATE ) )

group by 1,2,3,4

) svpr_dt
 on spma_dt.LogDate = svpr_dt.LogDate
 and spma_dt.LogTime = svpr_dt.LogTime
 and spma_dt.nodeid = svpr_dt.nodeid
 left join
 (
 sel
 thedate (format 'yyyy-mm-dd')(named "LogDate")
 ,cast(thetime as int) / 1000 * 1000 (format '99:99:99') (named "LogTime")
 ,600 (named "SPDSKInterval")
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

from dbc.resusagespdsk
 WHERE ( ( THEDATE = :BEGINDATE AND THETIME >= :BEGINTIME ) OR
 ( THEDATE > :BEGINDATE ) )
 AND
 ( ( THEDATE = :ENDDATE AND THETIME <= :ENDTIME ) OR
 ( THEDATE < :ENDDATE ) )
 group by 1,2,3,4

) spdsk_dt
 on spma_dt.LogDate = spdsk_dt.LogDate
 and spma_dt.LogTime = spdsk_dt.LogTime
 and spma_dt.nodeid = spdsk_dt.nodeid
 where info.infokey (NOT CS) = 'VERSION'
 group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20
 order by 5,14,21,22
 ;
 );