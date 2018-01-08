# Copyright (C) 2016 Antoine Carme <Antoine.Carme@Laposte.net>
# All rights reserved.

# This file is part of the Python Automatic Forecasting (PyAF) library and is made available under
# the terms of the 3 Clause BSD license

import pandas as pd
import numpy as np
import datetime as dt
import calendar

from . import Utils as tsutil

class cTimeInfo:
    # class data
    sRES_NONE = 0
    sRES_SECOND = 1
    sRES_MINUTE = 2
    sRES_HOUR = 3
    sRES_DAY = 4
    sRES_MONTH = 5
    sSecondsInResolution = {};
    sSecondsInResolution[sRES_NONE] = 0;
    sSecondsInResolution[sRES_SECOND] = 1;
    sSecondsInResolution[sRES_MINUTE] = 1 * 60;
    sSecondsInResolution[sRES_HOUR] = 1 * 60 * 60;
    sSecondsInResolution[sRES_DAY] = 1 * 60 * 60 * 24;
    sSecondsInResolution[sRES_MONTH] = 1 * 60 * 60 * 24 * 30;
    sDatePartComputer = {}
    sDatePartComputer["Second"] = lambda iTimeValue : iTimeValue.second
    sDatePartComputer["Minute"] = lambda iTimeValue : iTimeValue.minute
    sDatePartComputer["Hour"] = lambda iTimeValue : iTimeValue.hour
    sDatePartComputer["DayOfMonth"] = lambda iTimeValue : iTimeValue.day
    sDatePartComputer["DayOfWeek"] = lambda iTimeValue : iTimeValue.dayofweek
    sDatePartComputer["DayOfYear"] = lambda iTimeValue : iTimeValue.dayofyear
    sDatePartComputer["WeekOfYear"] = lambda iTimeValue : iTimeValue.weekofyear
    sDatePartComputer["MonthOfYear"] = lambda iTimeValue : iTimeValue.month        

    def __init__(self):
        self.mSignalFrame = pd.DataFrame()
        self.mTimeMin = None;
        self.mTimeMax = None;
        self.mTimeMinMaxDiff = None;
        self.mTimeDelta = None;
        self.mHorizon = None;        
        self.mResolution = cTimeInfo.sRES_NONE

    def info(self):
        lStr2 = "TimeVariable='" + self.mTime +"'";
        lStr2 += " TimeMin=" + str(self.mTimeMin) +"";
        lStr2 += " TimeMax=" + str(self.mTimeMax) +"";
        lStr2 += " TimeDelta=" + str(self.mTimeDelta) +"";
        lStr2 += " Estimation = (" + str(self.mEstimStart) + " , " + str(self.mEstimEnd) + ")";
        lStr2 += " Validation = (" + str(self.mValidStart) + " , " + str(self.mValidEnd) + ")";
        lStr2 += " Test = (" + str(self.mTestStart) + " , " + str(self.mTestEnd) + ")";
        lStr2 += " Horizon=" + str(self.mHorizon) +"";
        return lStr2;


    def to_json(self):
        dict1 = {};
        dict1["TimeVariable"] =  self.mTime;
        dict1["TimeMinMax"] =  [str(self.mSignalFrame[self.mTime].min()) ,
                                str(self.mSignalFrame[self.mTime].max())];
        dict1["Horizon"] =  self.mHorizon;
        return dict1;

    def addVars(self, df):
        df[self.mRowNumberColumn] = self.mSignalFrame[self.mRowNumberColumn]
        df[self.mTime] = self.mSignalFrame[self.mTime]
        df[self.mNormalizedTimeColumn] = self.mSignalFrame[self.mNormalizedTimeColumn]
        df[self.mSignal] = self.mSignalFrame[self.mSignal]
        df[self.mOriginalSignal] = self.mSignalFrame[self.mOriginalSignal]

    def get_time_dtype(self):
        # print(self.mTimeMax, type(self.mTimeMax))
        lType = np.dtype(self.mTimeMax);
        return lType;

    def cast_to_time_dtype(self, iTimeValue):
        lType1 = self.get_time_dtype();
        lTimeValue = np.array([iTimeValue]).astype(lType1)[0];
        return lTimeValue;

    def checkDateAndSignalTypesForNewDataset(self, df):
        if(self.mTimeMax is not None):
            lType1 = self.get_time_dtype();
            lType2 = np.dtype(df[self.mTime]);
            if(lType1.kind != lType2.kind):
                raise tsutil.PyAF_Error('Incompatible Time Column Type expected=' + str(lType1) + ' got: ' + str(lType2) + "'");
                pass
        

    def transformDataset(self, df):
        self.checkDateAndSignalTypesForNewDataset(df);
        # new row
        lLastRow = df.tail(1).copy();
        lLastRow[self.mTime] = self.nextTime(df, 1);
        lLastRow[self.mSignal] = np.nan;
        df = df.append(lLastRow, ignore_index=True, verify_integrity = True);        
        df[self.mRowNumberColumn] = np.arange(0, df.shape[0]);
        df[self.mNormalizedTimeColumn] = self.compute_normalize_date_column(df[self.mTime])
        # print(df.tail());
        return df;


    def isPhysicalTime(self):
        type1 = np.dtype(self.mSignalFrame[self.mTime])
        return (type1.kind == 'M');


    def get_date_part_value_computer(self , iDatePart):
        return cTimeInfo.sDatePartComputer[iDatePart];
    
    def analyzeSeasonals(self):
        if(not self.isPhysicalTime()):
            return;
        lEstim = self.getEstimPart(self.mSignalFrame);
        lEstimSecond = lEstim[self.mTime].apply(self.get_date_part_value_computer("Second"));
        if(lEstimSecond.nunique() > 1.0):
            self.mResolution = cTimeInfo.sRES_SECOND;
            return;
        lEstimMinute = lEstim[self.mTime].apply(self.get_date_part_value_computer("Minute"));
        if(lEstimMinute.nunique() > 1.0):
            self.mResolution =  cTimeInfo.sRES_MINUTE;
            return;
        lEstimHour = lEstim[self.mTime].apply(self.get_date_part_value_computer("Hour"));
        if(lEstimHour.nunique() > 1.0):
            self.mResolution =  cTimeInfo.sRES_HOUR;
            return;
        lEstimDayOfMonth = lEstim[self.mTime].apply(self.get_date_part_value_computer("DayOfMonth"));
        if(lEstimDayOfMonth.nunique() > 1.0):
            self.mResolution =  cTimeInfo.sRES_DAY;
            return;
        lEstimMonth = lEstim[self.mTime].apply(self.get_date_part_value_computer("MonthOfYear"));
        if(lEstimMonth.nunique() > 1.0):
            self.mResolution =  cTimeInfo.sRES_MONTH;
            return;

    def getSecondsInResolution(self):
        return cTimeInfo.sSecondsInResolution.get(self.mResolution , 0.0);

    def cutFrame(self, df):
        lFrameFit = df[self.mEstimStart : self.mEstimEnd];
        lFrameForecast = df[self.mValidStart : self.mValidEnd];
        lFrameTest = df[self.mTestStart : self.mTestEnd];
        return (lFrameFit, lFrameForecast, lFrameTest)

    def getEstimPart(self, df):
        lFrameFit = df[self.mEstimStart : self.mEstimEnd];
        return lFrameFit;

    def getValidPart(self, df):
        lFrameValid = df[self.mValidStart : self.mValidEnd];
        return lFrameValid;

    def defineCuttingParameters(self):
        lStr = "CUTTING_START SignalVariable='" + self.mSignal +"'";
        # print(lStr);
        #print(self.mSignalFrame.head())
        self.mTrainSize = self.mSignalFrame.shape[0];
        assert(self.mTrainSize > 0);
        lEstEnd = int((self.mTrainSize - self.mHorizon) * self.mOptions.mEstimRatio);
        lValSize = self.mTrainSize - self.mHorizon - lEstEnd;
        lTooSmall = False;
        # training too small
        if((self.mTrainSize < 30) or (lValSize < self.mHorizon)):
            lTooSmall = True;
        
        if(lTooSmall):
            self.mEstimStart = 0;
            self.mEstimEnd = self.mTrainSize;
            self.mValidStart = 0;
            self.mValidEnd = self.mTrainSize;
            self.mTestStart = 0;
            self.mTestEnd = self.mTrainSize;
        else:
            self.mEstimStart = 0;
            self.mEstimEnd = lEstEnd;
            self.mValidStart = self.mEstimEnd;
            self.mValidEnd = self.mTrainSize - self.mHorizon;
            self.mTestStart = self.mValidEnd;
            self.mTestEnd = self.mTrainSize;

        lStr = "CUTTING_PARAMETERS " + str(self.mTrainSize) + " Estimation = (" + str(self.mEstimStart) + " , " + str(self.mEstimEnd) + ")";
        lStr += " Validation = (" + str(self.mValidStart) + " , " + str(self.mValidEnd) + ")";
        lStr += " Test = (" + str(self.mTestStart) + " , " + str(self.mTestEnd) + ")";
        #print(lStr);
        
        pass

    def checkDateAndSignalTypes(self):
        # print(self.mSignalFrame.info());
        type1 = np.dtype(self.mSignalFrame[self.mTime])
        if(type1.kind == 'O'):
            raise tsutil.PyAF_Error('Invalid Time Column Type ' + self.mTime + '[' + str(type1) + ']');
        type2 = np.dtype(self.mSignalFrame[self.mSignal])
        if(type2.kind == 'O'):
            raise tsutil.PyAF_Error('Invalid Signal Column Type ' + self.mSignal);
        

    def isOneRowDataset(self):
        return ((1 + self.mEstimStart) ==  self.mEstimEnd)


    def adaptTimeDeltaToTimeResolution(self):
        if(not self.isPhysicalTime()):
            return;
        if(cTimeInfo.sRES_SECOND == self.mResolution):
            return;
        if(cTimeInfo.sRES_MINUTE == self.mResolution):
            self.mTimeDelta = round(self.mTimeDelta / np.timedelta64(1,'m')) * np.timedelta64(1,'m')
            return;
        if(cTimeInfo.sRES_HOUR == self.mResolution):
            self.mTimeDelta = round(self.mTimeDelta / np.timedelta64(1,'h')) * np.timedelta64(1,'h')
            return;
        if(cTimeInfo.sRES_DAY == self.mResolution):
            self.mTimeDelta = round(self.mTimeDelta / np.timedelta64(1,'D')) * np.timedelta64(1,'D')
            return;
        if(cTimeInfo.sRES_MONTH == self.mResolution):
            self.mTimeDelta = round(self.mTimeDelta / np.timedelta64(30,'D')) * np.timedelta64(30,'D')
            return;
        pass
    
    def get_lags_for_time_resolution(self):
        if(not self.isPhysicalTime()):
            return None;
        lARORder = {}
        lARORder[cTimeInfo.sRES_SECOND] = 60
        lARORder[cTimeInfo.sRES_MINUTE] = 60
        lARORder[cTimeInfo.sRES_HOUR] = 24
        lARORder[cTimeInfo.sRES_DAY] = 31
        lARORder[cTimeInfo.sRES_MONTH] = 12
        return lARORder.get(self.mResolution , None)
    
    def computeTimeDelta(self):
        #print(self.mSignalFrame.columns);
        # print(self.mSignalFrame[self.mTime].head());
        lEstim = self.mSignalFrame[self.mEstimStart : self.mEstimEnd]
        lTimeBefore = lEstim[self.mTime].shift(1);
        # lTimeBefore.fillna(self.mTimeMin, inplace=True)
        N = lEstim.shape[0];
        if(N == 1):
            if(self.isPhysicalTime()):
                self.mTimeDelta = np.timedelta64(1,'D');
            else:
                self.mTimeDelta = 1
            return
        #print(self.mSignal, self.mTime, N);
        #print(lEstim[self.mTime].head());
        #print(lTimeBefore.head());
        lDiffs = lEstim[self.mTime][1:N] - lTimeBefore[1:N]
        
        if(self.mOptions.mTimeDeltaComputationMethod == "USER"):
            self.mTimeDelta = self.mOptions.mUserTimeDelta;
        if(self.mOptions.mTimeDeltaComputationMethod == "AVG"):
            self.mTimeDelta = np.mean(lDiffs);
            type1 = np.dtype(self.mSignalFrame[self.mTime])
            if(type1.kind == 'i' or type1.kind == 'u'):
                self.mTimeDelta = int(self.mTimeDelta)
        if(self.mOptions.mTimeDeltaComputationMethod == "MODE"):
            delta_counts = pd.DataFrame(lDiffs.value_counts());
            self.mTimeDelta = delta_counts[self.mTime].argmax();
        self.adaptTimeDeltaToTimeResolution();

    def estimate(self):
        #print(self.mSignalFrame.columns);
        #print(self.mSignalFrame[self.mTime].head());
        self.checkDateAndSignalTypes();
        
        self.mRowNumberColumn = "row_number"
        self.mNormalizedTimeColumn = self.mTime + "_Normalized";

        self.defineCuttingParameters();

        self.analyzeSeasonals();

        lEstim = self.mSignalFrame[self.mEstimStart : self.mEstimEnd]
        self.mTimeMin = lEstim[self.mTime].min();
        self.mTimeMax = lEstim[self.mTime].max();
        if(self.isPhysicalTime()):
            self.mTimeMin = np.datetime64(self.mTimeMin.to_pydatetime());
            self.mTimeMax = np.datetime64(self.mTimeMax.to_pydatetime());
        self.mTimeMinMaxDiff = self.mTimeMax - self.mTimeMin;
        # print(self.mTimeMin, self.mTimeMax , self.mTimeMinMaxDiff , (self.mTimeMax - self.mTimeMin)/self.mTimeMinMaxDiff)
        self.computeTimeDelta();
        self.mSignalFrame[self.mNormalizedTimeColumn] = self.compute_normalize_date_column(self.mSignalFrame[self.mTime])
        self.dump();

    def dump(self):
        time_info = self.info(); 
        

    def compute_normalize_date_column(self, idate_column):
        if(self.isOneRowDataset()):
            return 0.0;
        return idate_column.apply(self.normalizeTime)

    @tsutil.cMemoize
    def normalizeTime(self , iTime):
        output =  ( iTime- self.mTimeMin) / self.mTimeMinMaxDiff
        return output

    def addMonths(self, iTime , iMonths):
        date_after_months = iTime + iMonths * (365.0/12) * np.timedelta64(1,'D')
        # print("addMonths" , iTime, iMonths, date_after_months);
        return date_after_months;
    
    def nextTime(self, df, iSteps):
        #print(df.tail(1)[self.mTime]);
        lLastTime = df[self.mTime].values[-1]
        # Better handle time delta in months
        # print("NEXT_TIME" , lLastTime, iSteps, self.mTimeDelta);
        lNextTime = lLastTime + iSteps * self.mTimeDelta;
        if(self.mResolution == cTimeInfo.sRES_MONTH):
            lMonths = iSteps * int(self.mTimeDelta / np.timedelta64(1,'D') / 30);
            lNextTime = self.addMonths(lLastTime, lMonths);
        if(self.mOptions.mBusinessDaysOnly):
            lOffset = [1, 1, 1, 1, 3, 2, 1][lNextTime.weekday()];
            lNextTime = lNextTime +  np.timedelta64(lOffset,'D') # dt.timedelta(days = lOffset);

        return lNextTime;
