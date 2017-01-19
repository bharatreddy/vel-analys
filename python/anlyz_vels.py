if __name__ == "__main__":
    import anlyz_vels
    import datetime
    stDate = datetime.datetime( 2011, 4, 9, 8, 0 )
    endDate = datetime.datetime( 2011, 4, 9, 9, 0 )
    inpLosVelFile = \
        "/home/bharat/Documents/code/vel-analys/data/formatted-vels.txt"
    inpSAPSDataFile = \
        "/home/bharat/Documents/code/vel-analys/data/processedSaps.txt"
    svObj = anlyz_vels.SapsVelUtils( inpLosVelFile, stDate, endDate, \
        inpSAPSDataFile=inpSAPSDataFile, timeInterval=10 )
    fitResDF = svObj.get_fit_results()
    fitResDF.reset_index(drop=True,inplace=True)
    # plotFileName = \
    #     "/home/bharat/Documents/code/vel-analys/figs/vels-mlt-time-test.pdf"
    plotFileNameVelMlt = \
    "/home/bharat/Documents/code/vel-analys/figs/vels-mlt-variations-test.pdf"
    # svObj.plot_mean_mlt_time(fitResDF, plotFileName)
    # svObj.plot_mean_vel_mlt(fitResDF, plotFileNameVelMlt)
    saveFileName = "/home/bharat/Documents/code/vel-analys/data/apr9data.txt"
    svObj.save_data(fitResDF,saveFileName)


class SapsVelUtils(object):
    """
    Given start datetime and end datetime
    analyze SAPS velocities
    """
    def __init__(self, losdataFile, startDate, endDate,\
     inpSAPSDataFile=None, timeInterval=10):
        import lshell_opt
        import datetime
        # We'll use the optimized lshell fitting to get fitted vels
        # set up the object
        self.lsObj = lshell_opt.LshellFit(\
            losdataFile, inpSAPSDataFile=inpSAPSDataFile)
        self.startDate = startDate
        self.endDate = endDate
        # loop through the datetimes
        delDates = endDate - startDate
        # loop through the dates and create a list
        self.dtList = []
        for dd in range((delDates.seconds)/(60*timeInterval) + 1):
            currDate = startDate + \
                datetime.timedelta( minutes=dd*timeInterval )
            self.dtList.append(currDate)

    def get_fit_results(self):
        import pandas
        """
        for the given datelist get the fit
        results from optimized lshell fit code
        """
        fitDFList = []
        cntTotalRows = 0
        for cd in self.dtList:
            print "working with time-->", cd
            currfitDF = self.lsObj.get_timewise_lshell_fits(cd)
            # To this DF add a datetime column, to distinguish between fits
            currfitDF["date"] = cd
            fitDFList.append( currfitDF )
            fitDF = pandas.concat( fitDFList )
        return fitDF

    def plot_mean_mlt_time(self, fitDF, plotName,\
         plotListMLTs=[ 23., 0., 1., 2., 3., 4.]):
        import pandas
        import matplotlib.pyplot as plt
        from matplotlib.dates import DateFormatter,\
             HourLocator, MinuteLocator
        import datetime
        """
        Given a list of MLTs, plot the mean velocities 
        observed in the MLTs as a function of time.
        """
        # We are working on normMLT so convert the given
        # MLT to normMLT
        inpNormMLT = []
        for pmt in plotListMLTs:
            if pmt >= 12.:
                inpNormMLT.append( pmt - 24. )
            else:
                inpNormMLT.append( pmt )
        # Narrow down the fit res DF to the selected MLT
        fitDF = fitDF[ fitDF["normMLT"].isin(inpNormMLT) \
            ].reset_index(drop=True)
        # Now groupby the DF on time and MLT to get mean velocities
        mltMeanVelsDF = fitDF.groupby( ["date","normMLT"]\
            ).mean().reset_index()
        # Now plot the velocities
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(8, 4))
        # set plot styling
        min_date = None
        max_date = None
        for cnm, nm in enumerate(inpNormMLT):
            currDF = mltMeanVelsDF[ mltMeanVelsDF["normMLT"] == nm ]
            currVels = currDF["vSaps"]
            dates = [ tt for tt in currDF["date"] ]
            ax.plot_date(x=dates, y=currVels, fmt='.-', label=str(plotListMLTs[cnm]) + " MLT",
                tz=None, xdate=True, ydate=False, linewidth=1.5, markersize=10.)
        # format the x tick marks
        ax.xaxis.set_major_formatter(DateFormatter('%H%M'))
        # ax.xaxis.set_minor_formatter(DateFormatter('\n%M'))
        ax.xaxis.set_major_locator(MinuteLocator(interval=20))
        # ax.xaxis.set_minor_locator(MinuteLocator(interval=10))
        # give a bit of space at each end of the plot - aesthetics
        extra = datetime.timedelta(minutes=0)
        ax.set_xlim([self.startDate - extra, self.endDate + extra])
        ax.set_ylim([0., 2500.])

        # grid, legend and yLabel
        ax.grid(True)
        ax.legend(loc='best', prop={'size':'x-small'})
        ax.set_ylabel('SAPS Velocities [m/s]')
        ax.set_xlabel('time')
        fig.savefig(plotName, dpi=125)

    def plot_mean_vel_mlt(self, fitDF, plotName,\
         avgTimeInterval=30):
        import time
        import datetime
        import pandas
        import matplotlib.pyplot as plt
        """
        In this function we plot mean velocities at different MLTs
        averaged over a time interval. Basically MLT variations at
        different times.
        """
        # Now we need to group the velocities by different time intervals
        # say we have 30 min intervals, we need to get means of all velocities
        # between 8 and 830 into 1 group, 830 and 9 to another and so on.
        # We'll get seperate minute buckets/bins to do the same!
        fitDF["timestamp"] = [ time.mktime(x.timetuple())\
                                        for x in fitDF['date'] ]
        # Now divide the timestamps into different bins based on
        # the time interval provided as the input!
        # Also need to convert the timeinterval to sec to 
        # work with timestamps.
        timeBins = []
        binLabels = []
        currTimeStamp = fitDF["timestamp"].min()
        while currTimeStamp <= fitDF["timestamp"].max():
            timeBins.append(currTimeStamp)
            currDtObj = datetime.datetime.fromtimestamp(currTimeStamp)
            if currTimeStamp == fitDF["timestamp"].min():
                prevBinLabel = currDtObj.strftime("%H%M")
            else:
                binLabels.append( prevBinLabel + "-" + currDtObj.strftime("%H%M") )
                prevBinLabel = currDtObj.strftime("%H%M")
            currTimeStamp += avgTimeInterval*60.
        # Apply the bins using pandas.cut functionality
        fitDF = pandas.concat( [ fitDF, \
                    pandas.cut( fitDF["timestamp"], \
                               bins=timeBins, include_lowest=True,\
                                labels=binLabels ) ], axis=1 )
        # Now we need to change the col names to accomodate the labels
        fitDF.columns = [ ["normMLT", "MLAT","vSaps", \
                     "azim", "vMagnErr", "azimErr", "vLosMean",\
                     "vLosMax", "goodFitCheck", "plot_MLATEnd",\
                      "plot_normMLTEnd", "date", "timestamp", "timebins"] ]
        # groupby the timebins and normMLTs and get mean velocities
        mltTimeMeanVelsDF = fitDF.groupby( ["timebins","normMLT"]\
            )["vSaps", "MLAT"].mean().reset_index()
        # get to the plotting part!
        plt.style.use('ggplot')
        fig, ax = plt.subplots(figsize=(8, 4))
        # set plot styling
        min_date = None
        max_date = None
        for ctb, tb in enumerate(binLabels):
            currDF = mltTimeMeanVelsDF[ mltTimeMeanVelsDF["timebins"] == tb ]
            currVels = currDF["vSaps"]
            currMlts = currDF["normMLT"]
            currMlats = currDF["MLAT"]
            # ax.plot(currMlts, currVels, fmt='.-', \
            #     label=tb + " UT", linewidth=1.5, markersize=10.)
            ax.plot(currMlts, currVels, ".-", label=tb + " UT",\
                 linewidth=1.5, markersize=10.)
        # plot formatting
        xlimRange = [ -3, 5 ]
        # Also MLT is in normalized format, get the proper MLT values!
        mltLabelsPlot = []
        for x in range( xlimRange[0], xlimRange[1]+1 ):
            if x < 0.:
                mltLabelsPlot.append( str(x + 24) )
            else:
                mltLabelsPlot.append( str(x) )
        ax.set_xlim([-3.,5.])
        ax.set_ylim([0., 2500.])
        ax.set_xticklabels(mltLabelsPlot)
        # grid, legend and yLabel
        ax.grid(True)
        ax.legend(loc='best', prop={'size':'x-small'})
        ax.set_ylabel('SAPS Velocities [m/s]')
        ax.set_xlabel('MLT')
        fig.savefig(plotName, dpi=125)

    def save_data(self, fitDF, saveFileName):
        """
        Save the fit results df as a csv/txt file
        The saved results can be used to make movies
        or used for future analysis!
        """
        import pandas
        # Now we need date and time seperately for idl
        fitDF["dtStr"] = [ x.strftime("%Y%m%d") for x in fitDF["date"]]
        fitDF["tmStr"] = [ x.strftime("%H%M") for x in fitDF["date"]]
        # select the columns to save
        fitDF = fitDF[ ["normMLT", "MLAT", "vSaps", "azim",\
             "vMagnErr", "azimErr", "dtStr", "tmStr"] ]
        # Save the DF to the given file
        fitDF.to_csv(saveFileName, sep=' ', index=False)