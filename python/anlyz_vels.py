if __name__ == "__main__":
    import anlyz_vels
    import datetime
    stDate = datetime.datetime( 2011, 4, 9, 7, 0 )
    endDate = datetime.datetime( 2011, 4, 9, 9, 30 )
    inpLosVelFile = \
        "/home/bharat/Documents/code/vel-analys/data/formatted-vels.txt"
    inpSAPSDataFile = \
        "/home/bharat/Documents/code/vel-analys/data/processedSaps.txt"
    svObj = anlyz_vels.SapsVels( inpLosVelFile, stDate, endDate, \
        inpSAPSDataFile=inpSAPSDataFile, timeInterval=10 )
    fitRestDF = svObj.get_fit_results()
    print "final Res--->", fitRestDF.shape
    print fitRestDF


class SapsVels(object):
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
        # for the given datelist get the fit
        # results from optimized lshell fit code
        fitDFList = []
        cntTotalRows = 0
        for cnt, cd in enumerate(self.dtList):
            currfitDF = self.lsObj.get_timewise_lshell_fits(cd)
            print "curr shape fit res---->", currfitDF.shape
            cntTotalRows += currfitDF.shape[0]
            if cnt == 0:
                fitDF = currfitDF
            else:
                fitDF.append( currfitDF )
        print "total rows----->", cntTotalRows
        return fitDF


