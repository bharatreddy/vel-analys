if __name__ == "__main__":
    import anlyz_vels
    import datetime
    stDate = datetime.datetime( 2011, 4, 9, 7, 0 )
    endDate = datetime.datetime( 2011, 4, 9, 10, 30 )
    inpLosVelFile = \
        "/home/bharat/Documents/code/vel-analys/data/formatted-vels.txt"
    inpSAPSDataFile = \
        "/home/bharat/Documents/code/vel-analys/data/processedSaps.txt"
    svObj = anlyz_vels.SapsVelUtils( inpLosVelFile, stDate, endDate, \
        inpSAPSDataFile=inpSAPSDataFile, timeInterval=2 )
    fitResDF = svObj.get_fit_results()
    fitResDF.reset_index(drop=True,inplace=True)
    plotFileName = \
        "/home/bharat/Documents/code/vel-analys/figs/vels-mlt-time-test.pdf"
    svObj.plot_mean_mlt_time(fitResDF, plotFileName)
    # svObj.plot_mean_vel_mlt(fitResDF, plotFileName)


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
        span = self.startDate - self.endDate
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
        import pandas
        import matplotlib.pyplot as plt
        """
        In this function we plot mean velocities at different MLTs
        averaged over a time interval
        """




