replace macro systemfe.gss_resusage_td200_pdcr
( BEGINDATE (DATE, DEFAULT DATE)
, ENDDATE 	(DATE, DEFAULT DATE)
, BEGINTIME (INT, DEFAULT 0)
, ENDTIME	  (INT, DEFAULT 240000)
)
AS (
sel
'TD20v1.0' (named "Version")
,spma_dt.LogDate (named "LogDate")
,cast(spma_dt.LogDay as char(3)) (named "LogDOW")
,spma_dt.LogTime (named "LogTime")
,cast((spma_dt.LogDate || ' ' || spma_dt.LogTime) as timestamp(0)) (named "Timestamp")
,extract(hour from "Timestamp") (named "Hour")
,extract(minute from "Timestamp") / 10 * 10 (named "Minute10")

,SPMANominalSecs (named "RSSInterval")         /* overall logging interval for 1 row per interval per cluster  */

/* System data */

,spma_dt.NodeType (Named "NodeGen")
,case when spma_dt.vproc1 > 0 then spma_dt.vproc1
 else 'PE-only Node'
end (Named "AMPS")
,nullifzero(spma_dt.NCPUs) (Named "CPUs")
,cast(info.infodata as varchar(20)) (named "DBSRelease")

,nullifzero(PM_COD) (Named "PMCOD")
,nullifzero(WM_COD) (Named "WMCOD")
,nullifzero(IO_COD) (Named "IOCOD")

,extract(minute from "Timestamp") (named "Minute01")
,extract(second from "Timestamp") (named "Seconds00")
,spma_dt.TDEnabledCPUs (named "ETcoreCPUs")
,diskspacev_dt.SumCurrPerm  (named "SumCurrPerm")
,diskspacev_dt.SumMaxPerm   (named "SumMaxPerm")
,diskspacev_dt.SumPeakSpool (named "SumPeakSpool")
,diskspacev_dt.SumPeakTemp  (named "SumPeakTemp")

/*** end grouping fields ***/

,min(MemSizeGB) (Named "MinMemSizeGB")
,max(MemSizeGB) (Named "MaxMemSizeGB")
,count(distinct(spma_dt.NodeID)) (Named "NumNodes")

/* SPMA data */

,sum(CPUUtil) / NumNodes / CPUs  (format 'ZZ9.9') (named "AvgCPUBusy")
,max(CPUUtil) / CPUs (format 'ZZ9.9') (named "MaxCPUBusy")
,sum(OSPctCPU) / NumNodes (format 'ZZ9.9') (named "AvgPctOSCPU")
,max(OSPctCPU)(format 'ZZ9.9') (named "MaxPctOSCPU")
,sum(IOWaitCPUUtil) / NumNodes / CPUs (format 'ZZ9.9') (named "AvgPctIOWait")
,sum(RunQSz) / NumNodes (format 'z,zz9.9') (named "AvgRunQSz")
,max(MaxRunQSz) (format 'z,zz9.9') (named "MaxRunQSz")
,max(IOWaitCPUUtil) / CPUs (format 'ZZ9.9') (named "MaxPctIOWait")
,zeroifnull( sum(SPMAPhysReads_cnt + SPMAPhysPreReads_cnt) /
nullifzero(sum(SPMAPhysReads_cnt + SPMAPhysPreReads_cnt + SPMAPhysWrites_cnt)) * 100) (format 'ZZ9.9') (named "PctReadsCnt")
,zeroifnull( sum(SPMAPhysReadKB_cnt + SPMAPhysPreReadKB_cnt) /
nullifzero(sum(SPMAPhysReadKB_cnt + SPMAPhysPreReadKB_cnt + SPMAPhysWriteKB_cnt)) * 100) (format 'ZZ9.9') (named "PctReadsKB")

,sum(SPMAPhysReads) / NumNodes (format 'ZZ,ZZ9.9') (named "AvgPosReadSec")
,sum(SPMAPhysPreReads) / NumNodes (format 'ZZ,ZZ9.9') (named "AvgPreReadSec")
,sum(SPMAPhysWrites) / NumNodes (format 'ZZ,ZZ9.9') (named "AvgWriteSec")

,sum(SPMAPhysReads + SPMAPhysPreReads + SPMAPhysWrites) / NumNodes (format 'ZZ,ZZ9.9') (named "AvgIOPsSecNode")
,max(SPMAPhysReads + SPMAPhysPreReads + SPMAPhysWrites) (format 'ZZ,ZZ9.9') (named "MaxIOPsSecNode")
,sum(SPMAPhysReadKB + SPMAPhysPreReadKB + SPMAPhysWriteKB) / 1024.0 / NumNodes (format 'ZZZ,ZZ9.9') (named "AvgMBSecNode")
,max(SPMAPhysReadKB + SPMAPhysPreReadKB + SPMAPhysWriteKB) / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxMBSecNode")
,sum(SPMAPhysReadKB + SPMAPhysPreReadKB) / 1024.0 / NumNodes (format 'ZZZ,ZZ9.9') (named "AvgReadMBSecNode")
,sum(SPMAPhysWriteKB) / 1024.0 / NumNodes (format 'ZZZ,ZZ9.9') (named "AvgWriteMBSecNode")

,sum(SPMAPhysReadKB + SPMAPhysPreReadKB + SPMAPhysWriteKB) / 1024.0 (format 'Z,ZZZ,ZZ9.9') (named "TtlMBSecGen")
,sum(SPMAPhysReadKB + SPMAPhysPreReadKB) / 1024.0 (format 'Z,ZZZ,ZZ9.9') (named "TtlReadMBSecGen")
,sum(SPMAPhysWriteKB) / 1024.0 (format 'Z,ZZZ,ZZ9.9') (named "TtlWriteMBSecGen")

,sum(SPMAPhysReads) (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "TtlPosReadSecGen")
,sum(SPMAPhysPreReads) (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "TtlPreReadSecGen")
,sum(SPMAPhysWrites) (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "TtlWriteSecGen")

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

,sum(LogPermDBRead) / NumNodes (format 'ZZ,ZZ9.9')(named "LogPermDBSecNode_SVPR")
,sum(LogPermCIRead) / NumNodes (format 'ZZ,ZZ9.9')(named "LogPermCISecNode_SVPR")
,sum(LogSpoolDBRead) / NumNodes (format 'ZZ,ZZ9.9')(named "LogSpoolDBSecNode_SVPR")
,sum(LogSpoolCIRead) / NumNodes (format 'ZZ,ZZ9.9')(named "LogSpoolCISecNode_SVPR")

,sum(PhySpoolDBRead) / NumNodes (format 'ZZ,ZZ9.9')(named "PhySpoolDBSecNode_SVPR")
,sum(PhySpoolCIRead) / NumNodes (format 'ZZ,ZZ9.9')(named "PhySpoolCISecNode_SVPR")
,sum(PhyPermDBRead) / NumNodes (format 'ZZ,ZZ9.9')(named "PhyPermDBSecNode_SVPR")
,sum(PhyPermCIRead) / NumNodes (format 'ZZ,ZZ9.9')(named "PhyPermCISecNode_SVPR")

,sum(LogPermRead) / NumNodes (format 'ZZ,ZZ9.9')(named "LogPermReadSecNode_SVPR")
,sum(LogSpoolRead) / NumNodes (format 'ZZ,ZZ9.9')(named "LogSpoolReadSecNode_SVPR")
,sum(LogPermReadKB) / 1024 / NumNodes (format 'ZZZ,ZZ9.9')(named "LogPermReadMBSecNode_SVPR")
,sum(LogSpoolReadKB) / 1024 / NumNodes (format 'ZZZ,ZZ9.9')(named "LogSpoolReadMBSecNode_SVPR")

,sum(PhyPermReadKB) / 1024 / NumNodes (format 'ZZZ,ZZ9.9')(named "PhyPermPosReadMBSecNode_SVPR")
,sum(PhyPermPreReadKB) / 1024 / NumNodes (format 'ZZZ,ZZ9.9')(named "PhyPermPreReadMBSecNode_SVPR")
,sum(PhySpoolReadKB) / 1024 / NumNodes (format 'ZZZ,ZZ9.9')(named "PhySpoolPosReadMBSecNode_SVPR")
,sum(PhySpoolPreReadKB) / 1024 / NumNodes (format 'ZZZ,ZZ9.9')(named "PhySpoolPreReadMBSecNode_SVPR")

,sum(PhyPermRead) / NumNodes (format 'ZZ,ZZ9.9')(named "PhyPermPosReadSecNode_SVPR")
,sum(PhyPermPreRead) / NumNodes (format 'ZZ,ZZ9.9')(named "PhyPermPreReadSecNode_SVPR")
,sum(PhySpoolRead) / NumNodes (format 'ZZ,ZZ9.9')(named "PhySpoolPosReadSecNode_SVPR")
,sum(PhySpoolPreRead) / NumNodes (format 'ZZ,ZZ9.9')(named "PhySpoolPreReadSecNode_SVPR")

,sum(PhyPermWrite) / NumNodes (format 'ZZ,ZZ9.9')(named "PhyPermWriteSecNode_SVPR")
,sum(PhySpoolWrite) / NumNodes (format 'ZZ,ZZ9.9')(named "PhySpoolWriteSecNode_SVPR")
,sum(PhyPermWriteKB) / 1024.0 / NumNodes (format 'ZZZ,ZZ9.9')(named "PhyPermWriteMBSecNode_SVPR")
,sum(PhySpoolWriteKB) / 1024.0 / NumNodes (format 'ZZZ,ZZ9.9')(named "PhySpoolWriteMBSecNode_SVPR")

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

,sum(FCRRequests) / NumNodes (format 'ZZ,ZZ9.9')(named "CylReadRequestsSecNode_SVPR")
,sum(SuccessfulFCRs) / NumNodes (format 'ZZ,ZZ9.9')(named "CylReadSecNode_SVPR")
,sum(FCRBlocksRead) / NumNodes (format 'ZZ,ZZZ,ZZ9.9') (named "CylReadBlocksSecNode_SVPR")
,sum(FCRDeniedThresh) / NumNodes (format 'ZZ,ZZ9.9') (named "CylReadDenThrSecNode_SVPR")
,sum(FCRDeniedCache)  / NumNodes (format 'ZZ,ZZ9.9')(named "CylReadDenCacheSecNode_SVPR")

,sum(PermDirtyRelease) / NumNodes (named "PermDirtyRelSecNode_SVPR")
,sum(PermCleanRelease) / NumNodes (named "PermCleanRelSecNode_SVPR")
,sum(PermDirtyReleaseKB) / 1024.0 / NumNodes (named "PermDirtyRelMBSecNode_SVPR")
,sum(PermCleanReleaseKB) / 1024.0 / NumNodes (named "PermCleanRelMBSecNode_SVPR")
,sum(PermDirtyAgedWriteKB) / 1024.0 / NumNodes (named "PermAgedWriteMBSecNode_SVPR")

,sum(SpoolDirtyRelease) / NumNodes (named "SpoolDirtyRelSecNode_SVPR")
,sum(SpoolCleanRelease) / NumNodes (named "SpoolCleanRelSecNode_SVPR")
,sum(SpoolDirtyReleaseKB) / 1024.0 / NumNodes (named "SpoolDirtyRelMBSecNode_SVPR")
,sum(SpoolCleanReleaseKB) / 1024.0 / NumNodes (named "SpoolCleanRelMBSecNode_SVPR")
,sum(SpoolDirtyAgedWriteKB) / 1024.0 / NumNodes (named "SpoolAgedWriteMBSecNode_SVPR")

,sum(WALTJWriteKB)  / 1024.0 / NumNodes (named "WALTJWriteMBSecNode_SVPR")
,sum(WALTJDirtyReleaseKB)  / 1024.0 / NumNodes (named "WALTJDirtyRelMBSecNode_SVPR")
,sum(PhysWALTJReadKB) / 1024.0 / NumNodes (named "PhysWALTJReadMBSecNode_SVPR")

/* SPMA Physical Bynet */

,sum(PtPReads) / NumNodes (format 'ZZ,ZZ9.9')(named "AvgPtPReadsSec")
,max(PtPReads) (format 'ZZ,ZZ9.9')(named "MaxPtPReadsSec")
,sum(PtPWrites) / NumNodes (format 'ZZ,ZZ9.9')(named "AvgPtPWritesSec")
,max(PtPWrites) (format 'ZZ,ZZ9.9')(named "MaxPtPWritesSec")

,sum(PtPReadKB) / 1024 / NumNodes (format 'ZZZ,ZZ9.9')(named "AvgPtPReadMBSec")
,max(PtPReadKB) / 1024 (format 'ZZZ,ZZ9.9')(named "MaxPtPReadMBSec")
,sum(PtPWriteKB) / 1024 / NumNodes (format 'ZZZ,ZZ9.9')(named "AvgPtPWriteMBSec")
,max(PtPWriteKB) / 1024 (format 'ZZZ,ZZ9.9')(named "MaxPtPWriteMBSec")

,sum(BrdReads) / NumNodes (format 'ZZ,ZZ9.9')(named "AvgBrdReadsSec")
,max(BrdReads) (format 'ZZ,ZZ9.9')(named "MaxBrdReadsSec")
,sum(BrdWrites) / NumNodes (format 'ZZ,ZZ9.9')(named "AvgBrdWritesSec")
,max(BrdWrites) (format 'ZZ,ZZ9.9')(named "MaxBrdWritesSec")

,sum(BrdReadKB) / 1024 / NumNodes (format 'ZZ,ZZ9.9')(named "AvgBrdReadMBSec")
,max(BrdReadKB) / 1024 (format 'ZZZ,ZZ9.9')(named "MaxBrdReadMBSec")
,sum(BrdWriteKB) / 1024 / NumNodes (format 'ZZ,ZZ9.9')(named "AvgBrdWriteMBSec")
,max(BrdWriteKB) / 1024 (format 'ZZZ,ZZ9.9')(named "MaxBrdWriteMBSec")

/* SPMA memory and swapping */

,sum(MemFreeKB) / NumNodes (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "AvgNodeMemFreeKB")
,min(MinMemFreeKB) (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "MinMemFreeKB")
,max(MaxMemFreeKB) (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "MaxMemFreeKB")

,sum(MemCtxtPageReads) / NumNodes (format 'Z,ZZ9.9')(named "AvgPgSwapInSec")
,max(MemCtxtPageReads) (format 'Z,ZZ9.9')(named "MaxPgSwapInSec")
,sum(MemCtxtPageWrites) / NumNodes (format 'Z,ZZ9.9')(named "AvgPgSwapOutSec")
,max(MemCtxtPageWrites) (format 'Z,ZZ9.9')(named "MaxPgSwapOutSec")

,sum(PageMinorFaults) / NumNodes (format 'Z,ZZ9.9')(named "AvgPageMinorFaultsSec")
,max(PageMinorFaults) (format 'Z,ZZ9.9')(named "MaxPageMinorFaultsSec")

/* SPDSK TVS */

,sum(HDDReadKB) / NumNodes / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgHDDReadMBSecNode_SPDSK")
,max(HDDReadKB) / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxHDDReadMBSecNode_SPDSK")
,sum(HDDWriteKB) / NumNodes / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgHDDWriteMBSecNode_SPDSK")
,max(HDDWriteKB) / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxHDDWriteMBSecNode_SPDSK")
,sum(HDDReads) / NumNodes (format 'ZZ,ZZZ,ZZ9.9') (named "AvgHDDReadsSecNode_SPDSK")
,max(HDDReads)   (format 'ZZ,ZZZ,ZZ9.9') (named "MaxHDDReadsSecNode_SPDSK")
,sum(HDDWrites) / NumNodes (format 'ZZ,ZZZ,ZZ9.9') (named "AvgHDDWritesSecNode_SPDSK")
,max(HDDWrites)   (format 'ZZ,ZZZ,ZZ9.9') (named "MaxHDDWritesSecNode_SPDSK")
,zeroifnull(sum(HDDTotReadResp / nullifzero(HDDReads_cnt)) * 10) (format 'Z,ZZ9.9') (named "AvgHDDReadResp")
,max(HDDReadRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxHDDReadResp")
,zeroifnull(sum(HDDTotWriteResp / nullifzero(HDDWrites_cnt)) * 10) (format 'Z,ZZ9.9') (named "AvgHDDWriteResp")
,max(HDDWriteRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxHDDWriteResp")

,sum(SSDReadKB) / NumNodes / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgSSDReadMBSecNode_SPDSK")
,max(SSDReadKB) / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxSSDReadMBSecNode_SPDSK")
,sum(SSDWriteKB) / NumNodes / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgSSDWriteMBSecNode_SPDSK")
,max(SSDWriteKB) / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxSSDWriteMBSecNode_SPDSK")
,sum(SSDReads) / NumNodes (format 'ZZ,ZZZ,ZZ9.9') (named "AvgSSDReadsSecNode_SPDSK")
,max(SSDReads) (format 'ZZ,ZZZ,ZZ9.9') (named "MaxSSDReadsSecNode_SPDSK")
,sum(SSDWrites) / NumNodes (format 'ZZ,ZZZ,ZZ9.9') (named "AvgSSDWritesSecNode_SPDSK")
,max(SSDWrites) (format 'ZZ,ZZZ,ZZ9.9') (named "MaxSSDWritesSecNode_SPDSK")
,zeroifnull(sum(SSDTotReadResp / nullifzero(SSDReads_cnt)) * 10) (format 'Z,ZZ9.9') (named "AvgSSDReadResp")
,max(SSDReadRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxSSDReadResp")
,zeroifnull(sum(SSDTotWriteResp / nullifzero(SSDWrites_cnt)) * 10) (format 'Z,ZZ9.9') (named "AvgSSDWriteResp")
,max(SSDWriteRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxSSDWriteResp")

,sum(WISSDReadKB) / NumNodes / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgWISSDReadMBSecNode_SPDSK")
,max(WISSDReadKB) / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxWISSDReadMBSecNode_SPDSK")
,sum(WISSDWriteKB) / NumNodes / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgWISSDWriteMBSecNode_SPDSK")
,max(WISSDWriteKB) / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxWISSDWriteMBSecNode_SPDSK")
,sum(WISSDReads) / NumNodes (format 'ZZ,ZZZ,ZZ9.9') (named "AvgWISSDReadsSecNode_SPDSK")
,max(WISSDReads) (format 'ZZ,ZZZ,ZZ9.9') (named "MaxWISSDReadsSecNode_SPDSK")
,sum(WISSDWrites) / NumNodes (format 'ZZ,ZZZ,ZZ9.9') (named "AvgWISSDWritesSecNode_SPDSK")
,max(WISSDWrites) (format 'ZZ,ZZZ,ZZ9.9') (named "MaxWISSDWritesSecNode_SPDSK")
,zeroifnull(sum(WISSDTotReadResp / nullifzero(WISSDReads_cnt)) * 10) (format 'Z,ZZ9.9') (named "AvgWISSDReadResp")
,max(WISSDReadRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxWISSDReadResp")
,zeroifnull(sum(WISSDTotWriteResp / nullifzero(WISSDWrites_cnt)) * 10) (format 'Z,ZZ9.9') (named "AvgWISSDWriteResp")
,max(WISSDWriteRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxWISSDWriteResp")

,sum(RISSDReadKB) / NumNodes / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgRISSDReadMBSecNode_SPDSK")
,max(RISSDReadKB) / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxRISSDReadMBSecNode_SPDSK")
,sum(RISSDWriteKB) / NumNodes / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgRISSDWriteMBSecNode_SPDSK")
,max(RISSDWriteKB) / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxRISSDWriteMBSecNode_SPDSK")
,sum(RISSDReads) / NumNodes (format 'ZZ,ZZZ,ZZ9.9') (named "AvgRISSDReadsSecNode_SPDSK")
,max(RISSDReads) (format 'ZZ,ZZZ,ZZ9.9') (named "MaxRISSDReadsSecNode_SPDSK")
,sum(RISSDWrites) / NumNodes (format 'ZZ,ZZZ,ZZ9.9') (named "AvgRISSDWritesSecNode_SPDSK")
,max(RISSDWrites) (format 'ZZ,ZZZ,ZZ9.9') (named "MaxRISSDWritesSecNode_SPDSK")
,zeroifnull(sum(RISSDTotReadResp / nullifzero(RISSDReads_cnt)) * 10) (format 'Z,ZZ9.9') (named "AvgRISSDReadResp")
,max(RISSDReadRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxRISSDReadResp")
,zeroifnull(sum(RISSDTotWriteResp / nullifzero(RISSDWrites_cnt)) * 10) (format 'Z,ZZ9.9') (named "AvgRISSDWriteResp")
,max(RISSDWriteRespMax) * 10 (format 'Z,ZZ9.9') (named "MaxRISSDWriteResp")

/* SVPR Logical CPU */

,sum(TotalPECPUBusy) / NumNodes / CPUs (format 'ZZ9.9') (named "AvgPECPUBusy")
,max(TotalPECPUBusy) / CPUs (format 'ZZ9.9') (named "MaxPECPUBusy")
,sum(TotalGTWCPUBusy) / NumNodes / CPUs (format 'ZZ9.9') (named "AvgGTWCPUBusy")
,max(TotalGTWCPUBusy) / CPUs (format 'ZZ9.9') (named "MaxGTWCPUBusy")
,sum(TotalAMPCPUBusy) / NumNodes / CPUs (format 'ZZ9.9') (named "AvgAMPCPUBusy")
,max(TotalAMPCPUBusy) / CPUs (format 'ZZ9.9') (named "MaxAMPCPUBusy")
,sum(TotalGTW_PECPUBusy) / NumNodes / CPUs (format 'ZZ9.9') (named "AvgGTW_PECPUBusy")
,max(TotalGTW_PECPUBusy) / CPUs (format 'ZZ9.9') (named "MaxGTW_PECPUBusy")

/* SVPR VH Cache */

,sum(VHAgedOut) / NumNodes (format 'ZZ,ZZ9.9')(named "AvgVHAgedOut_SVPR")
,sum(VHAgedOutKB) / NumNodes / 1024.0 (format 'ZZ,ZZ9.9')(named "AvgVHAgedOutMBSecNode_SVPR")
,sum(VHAcqs) / NumNodes (format 'ZZ,ZZ9.9')(named "AvgLogVHReads_SVPR")
,sum(VHAcqKB) / NumNodes / 1024.0 (format 'ZZ,ZZ9.9')(named "AvgLogVHReadMBSecNode_SVPR")
,sum(VHAcqReads) / NumNodes (format 'ZZ,ZZ9.9')(named "AvgPhysVHReads_SVPR")
,sum(VHAcqReadKB) / NumNodes / 1024.0 (format 'ZZ,ZZ9.9')(named "AvgPhysVHReadMBSecNode_SVPR")

/* SVPR Compression */

,sum(PreCompMB) / NumNodes (named "PreCompMBSecNode_SVPR")
,sum(PostCompMB) / NumNodes (named "PostCompMBSecNode_SVPR")
,sum(PreUnCompMB) / NumNodes (named "PreUnCompMBSecNode_SVPR")
,sum(PostUnCompMB) / NumNodes (named "PostUnCompMBSecNode_SVPR")
,sum(CompDBs) / NumNodes (named "CompDBsSecNode_SVPR")
,sum(UnCompDBs) / NumNodes (named "UnCompDBsSecNode_SVPR")

,sum(CompCPUMS_cnt) (named "COMPCPU")
,sum(UnCompCPUMS_cnt) (named "UNCOMPCPU")

,sum(CompCPUMS) / 10 / NumNodes / CPUs  (named "PctCPUComp")
,sum(UnCompCPUMS) / 10 / NumNodes / CPUs  (named "PctCPUUnComp")

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

,zeroifnull(sum(CompCPUMS) / NumNodes / nullifzero(PreCompMBSecNode_SVPR))  (named "CPUMSMBComp")
,zeroifnull(sum(UnCompCPUMS) / NumNodes / nullifzero(PostUnCompMBSecNode_SVPR))  (named "CPUMSMBUnComp")

/* SVPR NCS Node sizing */

,AvgGTW_PECPUBusy / 100 * NumNodes * CPUs / 2 / (PMCOD / 100) / 100 (named "TotalTCPUForNCSNodes")
,AvgGTW_PECPUBusy / 100 * NumNodes * CPUs / 2 / (PMCOD / 100) / 100 (named "AvgTCPUForNCSNode")
,MaxGTW_PECPUBusy / 100 * NumNodes * CPUs / 2 / (PMCOD / 100) / 100 (named "MaxTCPUForNCSNode")

/* SPMA host ntw traffic */

,sum(NtwReadKB) / NumNodes / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgNtwReadMBSecNode")
,max(NtwReadKB) / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxNtwReadMBSecNode")

,sum(NtwWriteKB) / NumNodes / 1024.0 (format 'ZZZ,ZZ9.9') (named "AvgNtwWriteMBSecNode")
,max(NtwWriteKB) / 1024.0 (format 'ZZZ,ZZ9.9') (named "MaxNtwWriteMBSecNode")

,sum(NtwReadKB) / 1024.0 (format 'Z,ZZZ,ZZ9.9') (named "TotalNtwReadMBSecNode")
,sum(NtwWriteKB) / 1024.0 (format 'Z,ZZZ,ZZ9.9') (named "TotalNtwWriteMBSecNode")

/* SPMA NOS */

,sum(NosCPUTime) / NumNodes / CPUs  (format 'ZZ9.9') (named "AvgPctNosCPUTime")
,max(NosCPUTime) / CPUs  (format 'ZZ9.9') (named "MaxPctNosCPUTime")
,sum(NosTotalIOWaitTime) / NumNodes / CPUs  (format 'ZZ9.9') (named "AvgPctNosTotalIOWaitTime")
,max(NosTotalIOWaitTime) / CPUs  (format 'ZZ9.9') (named "MaxPctNosTotalIOWaitTime")
,max(NosMaxIOWaitTime) (format 'ZZZ,ZZZ,ZZZ,ZZZ,ZZ9.9') (named "MaxNosMaxIOWaitTime")
,sum(NosPhysReadIOs) / NumNodes  (format 'ZZ,ZZ9.9') (named "AvgNosPhysReadIOsSec")
,sum(NosPhysReadIOs)  (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "TtlNosPhysReadIOsSecGen")
,sum(NosPhysWriteIOs) / NumNodes  (format 'ZZ,ZZ9.9') (named "AvgNosPhysWriteIOsSec")
,sum(NosPhysWriteIOs)  (format 'Z,ZZZ,ZZZ,ZZ9.9') (named "TtlNosPhysWriteIOsSecGen")
,sum(NosPhysReadIOs + NosPhysWriteIOs) / NumNodes  (format 'ZZ,ZZ9.9') (named "AvgNosPhysIOPsSecNode")
,max(NosPhysReadIOs + NosPhysWriteIOs)  (format 'ZZ,ZZ9.9') (named "MaxNosPhysIOPsSecNode")
,zeroifnull( sum(NosPhysReadIOs_cnt) /
nullifzero(sum(NosPhysReadIOs_cnt + NosPhysWriteIOs_cnt)) * 100) (format 'ZZ9.9') (named "PctNosReadsCnt")
,sum(NosPhysReadIOKB) / 1024.0 / NumNodes  (format 'ZZZ,ZZ9.9') (named "AvgNosPhysReadIOMBSecNode")
,max(NosPhysReadIOKB) / 1024.0  (format 'ZZZ,ZZ9.9') (named "MaxNosPhysReadIOMBSecNode")
,sum(NosPhysWriteIOKB) / 1024.0 / NumNodes  (format 'ZZZ,ZZ9.9') (named "AvgNosPhysWriteIOMBSecNode")
,max(NosPhysWriteIOKB) / 1024.0  (format 'ZZZ,ZZ9.9') (named "MaxNosPhysWriteIOMBSecNode")
,sum(NosPhysReadIOKB + NosPhysWriteIOKB) / 1024.0 / NumNodes  (format 'ZZ,ZZ9.9') (named "AvgNosPhysIOMBSecNode")
,max(NosPhysReadIOKB + NosPhysWriteIOKB) / 1024.0  (format 'ZZ,ZZ9.9') (named "MaxNosPhysIOMBSecNode")
,zeroifnull( sum(NosPhysReadIOKB_cnt) /
nullifzero(sum(NosPhysReadIOKB_cnt + NosPhysWriteIOKB_cnt)) * 100) (format 'ZZ9.9') (named "PctNosReadsKB")
,sum(NosPhysReadIOKB + NosPhysWriteIOKB) / 1024.0  (format 'Z,ZZZ,ZZ9.9') (named "TtlNosPhyMBSecGen")
,sum(NosPhysReadIOKB) / 1024.0  (format 'Z,ZZZ,ZZ9.9') (named "TtlNosPhyReadMBSecGen")
,sum(NosPhysWriteIOKB) / 1024.0  (format 'Z,ZZZ,ZZ9.9') (named "TtlNosPhyWriteMBSecGen")
,zeroifnull( TtlNosPhyReadMBSecGen / nullifzero(TtlNosPhysReadIOsSecGen) * 1024.0 ) (format 'Z,ZZ9.9') (named "KBReadNos")
,zeroifnull( TtlNosPhyWriteMBSecGen / nullifzero(TtlNosPhysWriteIOsSecGen) * 1024.0 ) (format 'Z,ZZ9.9')(named "KBWriteNos")
,sum(NosRecordsReturnedKB) / 1024.0 / NumNodes  (format 'ZZZ,ZZ9.9') (named "AvgNosRecordsReturnedMBSecNode")
,max(NosRecordsReturnedKB) / 1024.0  (format 'ZZZ,ZZ9.9') (named "MaxNosRecordsReturnedMBSec")

/* SVPR NOS */

,sum(NosPhysReadIOs_SVPR) / NumNodes  (format 'ZZ,ZZ9.9')(named "PhyNosReadSecNode_SVPR")
,sum(NosPhysWriteIOs_SVPR) / NumNodes  (format 'ZZ,ZZ9.9')(named "PhyNosWriteSecNode_SVPR")
,sum(NosPhysReadIOKB_SVPR) / 1024.0 / NumNodes  (format 'ZZZ,ZZ9.9')(named "PhyNosReadMBSecNode_SVPR")
,sum(NosPhysWriteIOKB_SVPR) / 1024.0 / NumNodes  (format 'ZZZ,ZZ9.9')(named "PhyNosWriteMBSecNode_SVPR")
,sum(NosRecordsReturnedKB_SVPR) / 1024.0 / NumNodes  (format 'ZZZ,ZZ9.9')(named "NosRecordsReturnedMBSecNode_SVPR")
,sum(PENosCPUTime_SVPR) / NumNodes / CPUs  (format 'ZZ9.9') (named "AvgNosPECPUBusy_SVPR")
,max(PENosCPUTime_SVPR) / CPUs  (format 'ZZ9.9') (named "MaxNosPECPUBusy_SVPR")
,sum(PENosTotalIOWaitTime_SVPR) / NumNodes / CPUs  (format 'ZZ9.9') (named "AvgPEPctNosTotalIOWaitTime_SVPR")
,max(PENosTotalIOWaitTime_SVPR) / CPUs  (format 'ZZ9.9') (named "MaxPEPctNosTotalIOWaitTime_SVPR")
,max(PENosMaxIOWaitTime_SVPR) (format 'ZZZ,ZZZ,ZZZ,ZZZ,ZZ9.9') (named "MaxPENosMaxIOWaitTime_SVPR")
,sum(PENosPhysReadIOs_SVPR) / NumNodes  (format 'ZZ,ZZ9.9')(named "PhyPENosReadSecNode_SVPR")
,sum(PENosPhysWriteIOs_SVPR) / NumNodes  (format 'ZZ,ZZ9.9')(named "PhyPENosWriteSecNode_SVPR")
,sum(PENosPhysReadIOKB_SVPR) / 1024.0 / NumNodes  (format 'ZZZ,ZZ9.9')(named "PhyPENosReadMBSecNode_SVPR")
,sum(PENosPhysWriteIOKB_SVPR) / 1024.0 / NumNodes  (format 'ZZZ,ZZ9.9')(named "PhyPENosWriteMBSecNode_SVPR")
,sum(AMPNosCPUTime_SVPR) / NumNodes / CPUs  (format 'ZZ9.9') (named "AvgNosAMPCPUBusy_SVPR")
,max(AMPNosCPUTime_SVPR) / CPUs  (format 'ZZ9.9') (named "MaxNosAMPCPUBusy_SVPR")
,sum(AMPNosTotalIOWaitTime_SVPR) / NumNodes / CPUs  (format 'ZZ9.9') (named "AvgAMPPctNosTotalIOWaitTime_SVPR")
,max(AMPNosTotalIOWaitTime_SVPR) / CPUs  (format 'ZZ9.9') (named "MaxAMPPctNosTotalIOWaitTime_SVPR")
,max(AMPNosMaxIOWaitTime_SVPR) (format 'ZZZ,ZZZ,ZZZ,ZZZ,ZZ9.9') (named "MaxAMPNosMaxIOWaitTime_SVPR")
,sum(AMPNosPhysReadIOs_SVPR) / NumNodes  (format 'ZZ,ZZ9.9')(named "PhyAMPNosReadSecNode_SVPR")
,sum(AMPNosPhysWriteIOs_SVPR) / NumNodes  (format 'ZZ,ZZ9.9')(named "PhyAMPNosWriteSecNode_SVPR")
,sum(AMPNosPhysReadIOKB_SVPR) / 1024.0 / NumNodes  (format 'ZZZ,ZZ9.9')(named "PhyAMPNosReadMBSecNode_SVPR")
,sum(AMPNosPhysWriteIOKB_SVPR) / 1024.0 / NumNodes  (format 'ZZZ,ZZ9.9')(named "PhyAMPNosWriteMBSecNode_SVPR")

/* SVPR FSG cache waits */

,sum(SVPRFsgCacheWaits)       / NumNodes (format 'z,zz9.9')  (Named "AvgSVPRFsgCacheWaits")
,sum(SVPRFsgCacheWaitTime)    / NumNodes (format 'z,zz9.9')  (Named "AvgSVPRFsgCacheWaitTime")
,max(SVPRFsgCacheWaitTimeMax)                                (Named "MaxSVPRFsgCacheWaitTimeMax")

/* SPMA NodeMbs */

,avg(AvgNodeMBs)  (named "AvgNodeMBs")
,max(MaxNodeMBs)  (named "MaxNodeMBs")

,avg(AvgNodeMBs)/1.05     (named "Factored-Down AvgNodeMBs")
,max(MaxNodeMBs)/1.05     (named "Factored-Down MaxNodeMBs")

/* SPMA RunQ and Process Pending Blocks */

,avg(SPMAProcReady)                 / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcReady")
,max(SPMAProcReadyMax)                         (format 'z,zz9.9')         (Named  "MaxSPMAProcReadyMax")
,sum(SPMAProcPendDBLock)            / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendDBLock")
,sum(SPMAProcPendFsgLock)           / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendFsgLock")
,sum(SPMAProcPendFsgRead)           / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendFsgRead")
,sum(SPMAProcPendFsgWrite)          / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendFsgWrite")
,sum(SPMAProcPendMemAlloc)          / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendMemAlloc")
,sum(SPMAProcPendMisc)              / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendMisc")
,sum(SPMAProcPendMonitor)           / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendMonitor")
,sum(SPMAProcPendMonResume)         / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendMonResume")
,sum(SPMAProcPendNetRead)           / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendNetRead")
,sum(SPMAProcPendNetReadAwt)        / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendNetReadAwt")
,sum(SPMAProcPendNetThrottle)       / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendNetThrottle")
,sum(SPMAProcPendQnl)               / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendQnl")
,sum(SPMAProcPendSegLock)           / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcPendSegLock")
,sum(SPMAProcBlocked)               / NumNodes (format 'z,zz9.9')         (Named  "AvgSPMAProcBlocked")

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
,nullifzero(NominalSecs) (named "SPMAInterval")  -- changed Secs to NominalSecs for use in this derived table query
,NominalSecs (named "SPMANominalSecs")           -- for use in outer query
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

,sum(CPUUExec+CPUUServ)  / SPMAInterval (named "CPUUtil")
,zeroifnull(sum(CPUUServ) / nullifzero(sum(CPUUExec+CPUUServ)) * 100) (named "OSPctCPU")
,sum(CPUUServ)  / SPMAInterval (named "ServCPUUtil")
,sum(CPUIoWait)  / SPMAInterval (named "IOWaitCPUUtil")
,avg(ProcReady) (named "RunQSz")
,max(ProcReadyMax) (named "MaxRunQSz")

/* Physical I/O */

,sum(FileAcqReads)  / SPMAInterval  (named "SPMAPhysReads")
,sum(FilePreReads)  / SPMAInterval  (named "SPMAPhysPreReads")
,sum(FileWrites)  / SPMAInterval    (named "SPMAPhysWrites")
,sum(FileAcqReadKB)  / SPMAInterval (named "SPMAPhysReadKB")
,sum(FilePreReadKB)  / SPMAInterval (named "SPMAPhysPreReadKB")
,sum(FileWriteKB)  / SPMAInterval   (named "SPMAPhysWriteKB")

,sum(FileAcqReads)  (named "SPMAPhysReads_cnt")
,sum(FilePreReads)  (named "SPMAPhysPreReads_cnt")
,sum(FileWrites)    (named "SPMAPhysWrites_cnt")
,sum(FileAcqReadKB) (named "SPMAPhysReadKB_cnt")
,sum(FilePreReadKB) (named "SPMAPhysPreReadKB_cnt")
,sum(FileWriteKB)   (named "SPMAPhysWriteKB_cnt")

/* Physical Bynet Traffic */

,sum(NetMsgPtPReads)  / SPMAInterval (named "PtPReads")
,sum(NetMsgPtPWrites)  / SPMAInterval (named "PtPWrites")
,sum(NetMsgPtPReadKB)  / SPMAInterval (named "PtPReadKB")
,sum(NetMsgPtPWriteKB)  / SPMAInterval (named "PtPWriteKB")
,sum(NetMsgBrdReads)  / SPMAInterval (named "BrdReads")
,sum(NetMsgBrdWrites)  / SPMAInterval (named "BrdWrites")
,sum(NetMsgBrdReadKB)  / SPMAInterval (named "BrdReadKB")
,sum(NetMsgBrdWriteKB)  / SPMAInterval (named "BrdWriteKB")

/* memory and swapping */

,sum(MemFreeKB) (named "MemFreeKB")
,min(MemFreeKB) (named "MinMemFreeKB")
,max(MemFreeKB) (named "MaxMemFreeKB")

,sum(MemCtxtPageReads)   / SPMAInterval (named "MemCtxtPageReads")
,sum(MemCtxtPageWrites)  / SPMAInterval (named "MemCtxtPageWrites")
,sum(PageMinorFaults)    / SPMAInterval (named "PageMinorFaults")

/* VH Cache */

,sum(VHCacheKB) (named "VHCacheKB")
,max(VHCacheKB) (named "MaxVHCacheKB")

/* ntw traffic */

,sum(HostReadKB)  / SPMAInterval (named "NtwReadKB")
,sum(HostWriteKB)  / SPMAInterval (named "NtwWriteKB")

/* NOS */

,sum(case when TD_ISNAN(NosCPUTime) = 1 then 0 else NosCPUTime end)            / SPMAInterval (named "NosCPUTime")
,sum(case when TD_ISNAN(NosTotalIOWaitTime) = 1 then 0 else NosTotalIOWaitTime end )    / SPMAInterval (named "NosTotalIOWaitTime")
,max(case when TD_ISNAN(NosMaxIOWaitTime) = 1 then 0 else NosMaxIOWaitTime end )                     (named "NosMaxIOWaitTime")
,sum(case when TD_ISNAN(NosPhysReadIOs) = 1 then 0 else NosPhysReadIOs end )        / SPMAInterval (named "NosPhysReadIOs")
,sum(case when TD_ISNAN(NosPhysReadIOKB) = 1 then 0 else NosPhysReadIOKB end )       / SPMAInterval (named "NosPhysReadIOKB")
,sum(case when TD_ISNAN(NosPhysWriteIOs) = 1 then 0 else NosPhysWriteIOs end )       / SPMAInterval (named "NosPhysWriteIOs")
,sum(case when TD_ISNAN(NosPhysWriteIOKB) = 1 then 0 else NosPhysWriteIOKB end )      / SPMAInterval (named "NosPhysWriteIOKB")
,sum(case when TD_ISNAN(NosRecordsReturnedKB) = 1 then 0 else NosRecordsReturnedKB end )  / SPMAInterval (named "NosRecordsReturnedKB")
,sum(case when TD_ISNAN(NosPhysReadIOs) = 1 then 0 else NosPhysReadIOs end )                       (named "NosPhysReadIOs_cnt")
,sum(case when TD_ISNAN(NosPhysWriteIOs) = 1 then 0 else NosPhysWriteIOs end )                      (named "NosPhysWriteIOs_cnt")
,sum(case when TD_ISNAN(NosPhysReadIOKB) = 1 then 0 else NosPhysReadIOKB end )                      (named "NosPhysReadIOKB_cnt")
,sum(case when TD_ISNAN(NosPhysWriteIOKB) = 1 then 0 else NosPhysWriteIOKB end )                     (named "NosPhysWriteIOKB_cnt")

/* NodeMbs */
,avg(Nodembs)			(named "AvgNodeMBs")
,max(Nodembs)			(named "MaxNodeMBs")

/* Process Pending Blocks */

,avg(ProcReady)                              (Named "SPMAProcReady")
,max(ProcReadyMax)                           (Named "SPMAProcReadyMax")
,sum(ProcPendDBLock)          / SPMAInterval (Named "SPMAProcPendDBLock")
,sum(ProcPendFsgLock)         / SPMAInterval (Named "SPMAProcPendFsgLock")
,sum(ProcPendFsgRead)         / SPMAInterval (Named "SPMAProcPendFsgRead")
,sum(ProcPendFsgWrite)        / SPMAInterval (Named "SPMAProcPendFsgWrite")
,sum(ProcPendMemAlloc)        / SPMAInterval (Named "SPMAProcPendMemAlloc")
,sum(ProcPendMisc)            / SPMAInterval (Named "SPMAProcPendMisc")
,sum(ProcPendMonitor)         / SPMAInterval (Named "SPMAProcPendMonitor")
,sum(ProcPendMonResume)       / SPMAInterval (Named "SPMAProcPendMonResume")
,sum(ProcPendNetRead)         / SPMAInterval (Named "SPMAProcPendNetRead")
,sum(ProcPendNetReadAwt)      / SPMAInterval (Named "SPMAProcPendNetReadAwt")
,sum(ProcPendNetThrottle)     / SPMAInterval (Named "SPMAProcPendNetThrottle")
,sum(ProcPendQnl)             / SPMAInterval (Named "SPMAProcPendQnl")
,sum(ProcPendSegLock)         / SPMAInterval (Named "SPMAProcPendSegLock")
,sum(ProcBlocked)             / SPMAInterval (Named "SPMAProcBlocked")


from PDCRINFO.ResUsageSpma_hst
WHERE ( ( THEDATE = :BEGINDATE AND THETIME >= :BEGINTIME ) OR
( THEDATE > :BEGINDATE ) )
AND
( ( THEDATE = :ENDDATE AND THETIME <= :ENDTIME ) OR
( THEDATE < :ENDDATE ) )
group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14

) spma_dt left join

(
sel
thedate (format 'yyyy-mm-dd')(named "LogDate")
,cast(thetime as int) / 10 * 10      (format '99:99:99') (named "LogTime")
,nullifzero(NominalSecs) (named "SVPRInterval")  -- changed Secs to NominalSecs for use in this derived table query
,NodeID

,sum(FilePDbAcqs) / SVPRInterval (named "LogPermDBRead")
,sum(FilePCiAcqs) / SVPRInterval (named "LogPermCIRead")
,LogPermDBRead+LogPermCIRead (named "LogPermRead")

,sum(FileSDbAcqs) / SVPRInterval (named "LogSpoolDBRead")
,sum(FileSCiAcqs) / SVPRInterval (named "LogSpoolCIRead")
,LogSpoolDBRead+LogSpoolCIRead  (named "LogSpoolRead")

,sum(FilePDbAcqKB + FilePCiAcqKB) / SVPRInterval (named "LogPermReadKB")
,sum(FileSDbAcqKB + FileSCiAcqKB) / SVPRInterval (named "LogSpoolReadKB")

,sum(FilePDbAcqReads)  / SVPRInterval (named "PhyPermDBRead")
,sum(FilePCiAcqReads)  / SVPRInterval (named "PhyPermCIRead")
,PhyPermDBRead+PhyPermCIRead (named "PhyPermRead")

,sum(FilePDbPreReads + FilePCiPreReads)  / SVPRInterval (named "PhyPermPreRead")

,sum(FileSDbAcqReads)  / SVPRInterval (named "PhySpoolDBRead")
,sum(FileSCiAcqReads)  / SVPRInterval (named "PhySpoolCIRead")
,PhySpoolDBRead+PhySpoolCIRead (named "PhySpoolRead")

,sum(FileSDbPreReads + FileSCiPreReads)  / SVPRInterval (named "PhySpoolPreRead")

,sum(FilePDbAcqReadKB + FilePCiAcqReadKB)  / SVPRInterval (named "PhyPermReadKB")
,sum(FilePDbPreReadKB + FilePCiPreReadKB)  / SVPRInterval (named "PhyPermPreReadKB")
,sum(FileSDbAcqReadKB + FileSCiAcqReadKB)  / SVPRInterval (named "PhySpoolReadKB")
,sum(FileSDbPreReadKB + FileSCiPreReadKB)  / SVPRInterval (named "PhySpoolPreReadKB")

,sum(FilePDbFWrites + FilePCiFWrites)  / SVPRInterval (named "PhyPermWrite")
,sum(FileSDbFWrites + FileSCiFWrites)  / SVPRInterval (named "PhySpoolWrite")
,sum(FilePDbFWriteKB + FilePCiFWriteKB)  / SVPRInterval (named "PhyPermWriteKB")
,sum(FileSDbFWriteKB + FileSCiFWriteKB)  / SVPRInterval (named "PhySpoolWriteKB")

/* extra perm db svpr for caching & WAl/TJ I/O */

,sum(FilePDbDyRRels)  / SVPRInterval (named "PermDirtyRelease")
,sum(FilePDbCnRRels)  / SVPRInterval (named "PermCleanRelease")
,sum(FilePDbDyAWrites)  / SVPRInterval (named "PermDirtyAgedWrite")

,sum(FilePDbDyRRelKB)  / SVPRInterval (named "PermDirtyReleaseKB")
,sum(FilePDbCnRRelKB)  / SVPRInterval (named "PermCleanReleaseKB")
,sum(FilePDbDyAWriteKB)  / SVPRInterval (named "PermDirtyAgedWriteKB")

,sum(FileSDbDyRRels)  / SVPRInterval (named "SpoolDirtyRelease")
,sum(FileSDbCnRRels)  / SVPRInterval (named "SpoolCleanRelease")
,sum(FileSDbDyRRelKB)  / SVPRInterval (named "SpoolDirtyReleaseKB")
,sum(FileSDbCnRRelKB)  / SVPRInterval (named "SpoolCleanReleaseKB")
,sum(FileSDbDyAWriteKB)  / SVPRInterval (named "SpoolDirtyAgedWriteKB")

,sum(FileTJtFWriteKB)  / SVPRInterval (named "WALTJWriteKB")
,sum(FileTJtDyAWriteKB) / SVPRInterval (named "WALTJDirtyReleaseKB")
,sum(FileTJtPreReadKB+FileTJtAcqReadKB) / SVPRInterval (named "PhysWALTJReadKB")

/* BLC */

,sum(FilePreCompMB)  / SVPRInterval (named "PreCompMB")
,sum(FilePostCompMB)  / SVPRInterval (named "PostCompMB")
,sum(FilePreUnCompMB)  / SVPRInterval (named "PreUnCompMB")
,sum(FilePostUnCompMB)  / SVPRInterval (named "PostUnCompMB")
,sum(FileCompDBs)  / SVPRInterval (named "CompDBs")
,sum(FileUnCompDBs)  / SVPRInterval (named "UnCompDBs")
,sum(FileCompCPU) / 1000  / SVPRInterval (named "CompCPUMS")
,sum(FileUnCompCPU) / 1000  / SVPRInterval (named "UnCompCPUMS")
,sum(FileCompCPU) / 1000 (named "CompCPUMS_cnt")
,sum(FileUnCompCPU) / 1000 (named "UnCompCPUMS_cnt")

/* cyl read stuff */

,sum(FileFcrRequests)  / SVPRInterval (named "FCRRequests")
,sum(FileFcrRequests-FileFcrDeniedUser-FileFcrDeniedKern)  / SVPRInterval (named "SuccessfulFCRs")
,sum(FileFcrBlocksRead)  / SVPRInterval (named "FCRBlocksRead")
,sum(FileFcrDeniedThreshKern+FileFcrDeniedThreshUser)  / SVPRInterval (named "FCRDeniedThresh")
,sum(FileFcrDeniedCache)  / SVPRInterval (named "FCRDeniedCache")

/* Logical CPU stuff */

,sum(CASE WHEN VprType like 'PE%' THEN CPUUExecPart13 ELSE 0 END)  / SVPRInterval (named "PEDispExec")
,sum(CASE WHEN VprType like 'PE%' THEN CPUUServPart13 ELSE 0 END)  / SVPRInterval (named "PEDispServ")
,sum(CASE WHEN VprType like 'PE%' THEN CPUUExecPart14 ELSE 0 END)  / SVPRInterval (named "PEParsExec")
,sum(CASE WHEN VprType like 'PE%' THEN CPUUServPart14 ELSE 0 END)  / SVPRInterval (named "PEParsServ")
,sum(CASE WHEN VprType like 'PE%' THEN CPUUExecPart12 ELSE 0 END)  / SVPRInterval (named "PESessExec")
,sum(CASE WHEN VprType like 'PE%' THEN CPUUServPart12 ELSE 0 END)  / SVPRInterval (named "PESessServ")

,PEDispExec + PEDispServ + PEParsExec + PEParsServ + PESessExec + PESessServ (named "TotalPECPUBusy")

,sum(CASE WHEN VprType like 'GTW%' THEN CPUUExecPart10 ELSE 0 END)  / SVPRInterval (named "GTWExec")
,sum(CASE WHEN VprType like 'GTW%' THEN CPUUServPart10 ELSE 0 END)  / SVPRInterval (named "GTWServ")

,GTWExec + GTWServ (named "TotalGTWCPUBusy")

,TotalPECPUBusy + TotalGTWCPUBusy (named "TotalGTW_PECPUBusy")

,sum(CASE WHEN VprType like 'AMP%' THEN CPUUExecPart11 ELSE 0 END)  / SVPRInterval (named "AMPWorkTaskExec")
,sum(CASE WHEN VprType like 'AMP%' THEN CPUUServPart11 ELSE 0 END)  / SVPRInterval (named "AMPWorkTaskServ")

,AMPWorkTaskExec + AMPWorkTaskServ (named "TotalAMPCPUBusy")

/* VH cache */

,sum(VHAgedOut)  / SVPRInterval (named "VHAgedOut")
,sum(VHAgedOutKB)  / SVPRInterval (named "VHAgedOutKB")
,sum(VHLogicalDBRead)  / SVPRInterval (named "VHAcqs")
,sum(VHLogicalDBReadKB)  / SVPRInterval (named "VHAcqKB")
,sum(VHPhysicalDBRead)  / SVPRInterval (named "VHAcqReads")
,sum(VHPhysicalDBReadKB)  / SVPRInterval (named "VHAcqReadKB")

/* NOS */

,sum(case when TD_ISNAN(NosPhysReadIOs) = 1 then 0 else NosPhysReadIOs end )       / SVPRInterval  (named "NosPhysReadIOs_SVPR")
,sum(case when TD_ISNAN(NosPhysWriteIOs) = 1 then 0 else NosPhysWriteIOs end )      / SVPRInterval  (named "NosPhysWriteIOs_SVPR")
,sum(case when TD_ISNAN(NosPhysReadIOKB) = 1 then 0 else NosPhysReadIOKB end )      / SVPRInterval  (named "NosPhysReadIOKB_SVPR")
,sum(case when TD_ISNAN(NosPhysWriteIOKB) = 1 then 0 else NosPhysWriteIOKB end )     / SVPRInterval  (named "NosPhysWriteIOKB_SVPR")
,sum(case when TD_ISNAN(NosRecordsReturnedKB) = 1 then 0 else NosRecordsReturnedKB end ) / SVPRInterval  (named "NosRecordsReturnedKB_SVPR")
,sum(CASE WHEN VprType like 'PE%' THEN Case When TD_ISNAN(NosCPUTime) = 1 then 0 else NosCPUTime end  ELSE 0 END)          / SVPRInterval (named "PENosCPUTime_SVPR")
,sum(CASE WHEN VprType like 'PE%' THEN Case When TD_ISNAN(NosTotalIOWaitTime) = 1 then 0 else NosTotalIOWaitTime end  ELSE 0 END)  / SVPRInterval (named "PENosTotalIOWaitTime_SVPR")
,max(CASE WHEN VprType like 'PE%' THEN Case When TD_ISNAN(NosMaxIOWaitTime) = 1 then 0 else NosMaxIOWaitTime end  ELSE 0 END)                   (named "PENosMaxIOWaitTime_SVPR")
,sum(CASE WHEN VprType like 'PE%' THEN Case When  TD_ISNAN(NosPhysReadIOs) = 1 then 0 else NosPhysReadIOs end  ELSE 0 END)      / SVPRInterval (named "PENosPhysReadIOs_SVPR")
,sum(CASE WHEN VprType like 'PE%' THEN Case When TD_ISNAN(NosPhysWriteIOs) = 1 then 0 else NosPhysWriteIOs end  ELSE 0 END)     / SVPRInterval (named "PENosPhysWriteIOs_SVPR")
,sum(CASE WHEN VprType like 'PE%' THEN Case When TD_ISNAN(NosPhysReadIOKB) = 1 then 0 else NosPhysReadIOKB end  ELSE 0 END)     / SVPRInterval (named "PENosPhysReadIOKB_SVPR")
,sum(CASE WHEN VprType like 'PE%' THEN Case When TD_ISNAN(NosPhysWriteIOKB) = 1 then 0 else NosPhysWriteIOKB end  ELSE 0 END)    / SVPRInterval (named "PENosPhysWriteIOKB_SVPR")
,sum(CASE WHEN VprType like 'AMP%' THEN Case When TD_ISNAN(NosCPUTime) = 1 then 0 else NosCPUTime end  ELSE 0 END)         / SVPRInterval (named "AMPNosCPUTime_SVPR")
,sum(CASE WHEN VprType like 'AMP%' THEN Case When TD_ISNAN(NosTotalIOWaitTime) = 1 then 0 else NosTotalIOWaitTime end  ELSE 0 END) / SVPRInterval (named "AMPNosTotalIOWaitTime_SVPR")
,max(CASE WHEN VprType like 'AMP%' THEN Case When TD_ISNAN(NosMaxIOWaitTime) = 1 then 0 else NosMaxIOWaitTime end  ELSE 0 END)                  (named "AMPNosMaxIOWaitTime_SVPR")
,sum(CASE WHEN VprType like 'AMP%' THEN Case When TD_ISNAN(NosPhysReadIOs) = 1 then 0 else NosPhysReadIOs end  ELSE 0 END)     / SVPRInterval (named "AMPNosPhysReadIOs_SVPR")
,sum(CASE WHEN VprType like 'AMP%' THEN Case When TD_ISNAN(NosPhysWriteIOs) = 1 then 0 else NosPhysWriteIOs end  ELSE 0 END)    / SVPRInterval (named "AMPNosPhysWriteIOs_SVPR")
,sum(CASE WHEN VprType like 'AMP%' THEN Case When TD_ISNAN(NosPhysReadIOKB) = 1 then 0 else NosPhysReadIOKB end  ELSE 0 END)    / SVPRInterval (named "AMPNosPhysReadIOKB_SVPR")
,sum(CASE WHEN VprType like 'AMP%' THEN Case When TD_ISNAN(NosPhysWriteIOKB) = 1 then 0 else NosPhysWriteIOKB end  ELSE 0 END)   / SVPRInterval (named "AMPNosPhysWriteIOKB_SVPR")

/* FSG cache waits */

,sum(FsgCacheWaits)       / SVPRInterval     (Named "SVPRFsgCacheWaits")
,sum(FsgCacheWaitTime)    / SVPRInterval     (Named "SVPRFsgCacheWaitTime")
,max(FsgCacheWaitTimeMax)                    (Named "SVPRFsgCacheWaitTimeMax")


from PDCRINFO.ResUsageSvpr_hst
WHERE ( ( THEDATE = :BEGINDATE AND THETIME >= :BEGINTIME ) OR
( THEDATE > :BEGINDATE ) )
AND
( ( THEDATE = :ENDDATE AND THETIME <= :ENDTIME ) OR
( THEDATE < :ENDDATE ) )
group by 1,2,3,4

) svpr_dt
 on spma_dt.LogDate           = svpr_dt.LogDate
and spma_dt.LogTime           = svpr_dt.LogTime
and spma_dt.nodeid            = svpr_dt.nodeid

left join
(
sel
thedate (format 'yyyy-mm-dd')(named "LogDate")
,cast(thetime as int) / 10 * 10      (format '99:99:99') (named "LogTime")
,nullifzero(NominalSecs) (named "SPDSKInterval")  -- changed Secs to NominalSecs for use in this derived table query
,NodeID

,sum(case when PdiskType = 'DISK' then ReadKB else 0 END) / SPDSKInterval (named "HDDReadKB")
,sum(case when PdiskType = 'DISK' then WriteKB else 0 END) / SPDSKInterval  (named "HDDWriteKB")
,sum(case when PdiskType = 'DISK' then ReadCnt else 0 END) / SPDSKInterval (named "HDDReads")
,sum(case when PdiskType = 'DISK' then WriteCnt else 0 END) / SPDSKInterval (named "HDDWrites")
,sum(case when PdiskType = 'DISK' then ReadCnt else 0 END) (named "HDDReads_cnt")
,sum(case when PdiskType = 'DISK' then WriteCnt else 0 END) (named "HDDWrites_cnt")
,sum(case when PdiskType = 'DISK' then ReadRespTot else 0 END) (named "HDDTotReadResp")
,sum(case when PdiskType = 'DISK' then WriteRespTot else 0 END) (named "HDDTotWriteResp")
,max(case when PdiskType = 'DISK' then ReadRespMax else 0 END) (named "HDDReadRespMax")
,max(case when PdiskType = 'DISK' then WriteRespMax else 0 END) (named "HDDWriteRespMax")

,sum(case when PdiskType = 'SSD' then ReadKB else 0 END) / SPDSKInterval (named "SSDReadKB")
,sum(case when PdiskType = 'SSD' then WriteKB else 0 END) / SPDSKInterval (named "SSDWriteKB")
,sum(case when PdiskType = 'SSD' then ReadCnt else 0 END) / SPDSKInterval (named "SSDReads")
,sum(case when PdiskType = 'SSD' then WriteCnt else 0 END) / SPDSKInterval (named "SSDWrites")
,sum(case when PdiskType = 'SSD' then ReadCnt else 0 END) (named "SSDReads_cnt")
,sum(case when PdiskType = 'SSD' then WriteCnt else 0 END) (named "SSDWrites_cnt")
,sum(case when PdiskType = 'SSD' then ReadRespTot else 0 END) (named "SSDTotReadResp")
,sum(case when PdiskType = 'SSD' then WriteRespTot else 0 END) (named "SSDTotWriteResp")
,max(case when PdiskType = 'SSD' then ReadRespMax else 0 END) (named "SSDReadRespMax")
,max(case when PdiskType = 'SSD' then WriteRespMax else 0 END) (named "SSDWriteRespMax")

/* add RI/WI SSD breakdown */

,sum(case when PdiskType = 'WSSD' then ReadKB else 0 END) / SPDSKInterval (named "WISSDReadKB")
,sum(case when PdiskType = 'WSSD' then WriteKB else 0 END) / SPDSKInterval (named "WISSDWriteKB")
,sum(case when PdiskType = 'WSSD' then ReadCnt else 0 END) / SPDSKInterval (named "WISSDReads")
,sum(case when PdiskType = 'WSSD' then WriteCnt else 0 END) / SPDSKInterval (named "WISSDWrites")
,sum(case when PdiskType = 'WSSD' then ReadCnt else 0 END) (named "WISSDReads_cnt")
,sum(case when PdiskType = 'WSSD' then WriteCnt else 0 END) (named "WISSDWrites_cnt")
,sum(case when PdiskType = 'WSSD' then ReadRespTot else 0 END) (named "WISSDTotReadResp")
,sum(case when PdiskType = 'WSSD' then WriteRespTot else 0 END) (named "WISSDTotWriteResp")
,max(case when PdiskType = 'WSSD' then ReadRespMax else 0 END) (named "WISSDReadRespMax")
,max(case when PdiskType = 'WSSD' then WriteRespMax else 0 END) (named "WISSDWriteRespMax")

,sum(case when PdiskType = 'RSSD' then ReadKB else 0 END) / SPDSKInterval (named "RISSDReadKB")
,sum(case when PdiskType = 'RSSD' then WriteKB else 0 END) / SPDSKInterval (named "RISSDWriteKB")
,sum(case when PdiskType = 'RSSD' then ReadCnt else 0 END) / SPDSKInterval (named "RISSDReads")
,sum(case when PdiskType = 'RSSD' then WriteCnt else 0 END) / SPDSKInterval (named "RISSDWrites")
,sum(case when PdiskType = 'RSSD' then ReadCnt else 0 END) (named "RISSDReads_cnt")
,sum(case when PdiskType = 'RSSD' then WriteCnt else 0 END) (named "RISSDWrites_cnt")
,sum(case when PdiskType = 'RSSD' then ReadRespTot else 0 END) (named "RISSDTotReadResp")
,sum(case when PdiskType = 'RSSD' then WriteRespTot else 0 END) (named "RISSDTotWriteResp")
,max(case when PdiskType = 'RSSD' then ReadRespMax else 0 END) (named "RISSDReadRespMax")
,max(case when PdiskType = 'RSSD' then WriteRespMax else 0 END) (named "RISSDWriteRespMax")

from PDCRINFO.ResUsageSpdsk_hst
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
where  info.infokey (NOT CS) = 'VERSION' (NOT CS)
group by 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22
order by "Timestamp"
;
);