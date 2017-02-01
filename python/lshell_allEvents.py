def str_to_datetime(row):
        # Given a datestr and a time string convert to a python datetime obj.
        import datetime
        datecolName="dateStr"
        timeColName="timeStr"
        currDateStr = str( int( row[datecolName] ) )
    #     return currDateStr
        if row[timeColName] < 10:
            currTimeStr = "000" + str( int( row[timeColName] ) )
        elif row[timeColName] < 100:
            currTimeStr = "00" + str( int( row[timeColName] ) )
        elif row[timeColName] < 1000:
            currTimeStr = "0" + str( int( row[timeColName] ) )
        else:
            currTimeStr = str( int( row[timeColName] ) )
        return datetime.datetime.strptime( currDateStr\
                        + ":" + currTimeStr, "%Y%m%d:%H%M" )

if __name__ == "__main__":
    """
    In the current code we'll loop through each and every
    file (representing l-o-s velocities for a given day)
    and get the best lshell fits out of them!!!
    """
    import pandas
    import datetime
    import os
    import lshell_opt
    # Base directory where all the files are stored
    baseDir = "/home/bharat/Documents/code/frmtd-vels/"
    # Output file to store the results
    fitResFile = "/home/bharat/Documents/code/vel-analys/data/all_fitted_vels.txt"
    # Before appending to the file! delete it if it 
    # exists already. We dont want to append to old data!
    if os.path.isfile( fitResFile ):
        os.remove( fitResFile )
    # SAPS data file
    inpSAPSDataFile = \
        "/home/bharat/Documents/code/vel-analys/data/processedSaps.txt"
    # Time interval to loop through
    timeInterval = 2 # min
    for root, dirs, files in os.walk(baseDir):
        for fName in files:
            currInpLosFile = root + fName    
            print "working with--->", currInpLosFile
            # Now get the fitted results for the curren tdate
            lsObj = lshell_opt.LshellFit(currInpLosFile,\
             inpSAPSDataFile=inpSAPSDataFile)
            # Need to figure out the minmum and max time
            # to loop through for each file!
            inpColNames = [ "dateStr", "timeStr", "beam", "range", \
              "azim", "Vlos", "MLAT", "MLON", "MLT", "radId", \
              "radCode"]
            tempDF = pandas.read_csv(currInpLosFile, sep=' ',\
                                         header=None, names=inpColNames)
            # add a datetime col
            # tempDF["date"] = pandas.to_datetime( \
            #                         tempDF['dateStr'].astype(str) + "-" +\
            #                         tempDF['timeStr'].astype(str), \
            #                         format='%Y%m%d-%H%M')
            tempDF["date"] = tempDF.apply( str_to_datetime, axis=1 )
            currStartDate = tempDF["date"].min()
            currEndDate = tempDF["date"].max()
            # loop through the datetimes
            delDates = currEndDate - currStartDate
            # loop through the dates and create a list
            fitDFList = []
            fitDF = None
            for dd in range((delDates.seconds)/(60*timeInterval) + 1):
                currDate = currStartDate + \
                    datetime.timedelta( minutes=dd*timeInterval )
                print "working with time-->", currDate
                currfitDF = lsObj.get_timewise_lshell_fits(currDate)
                if currfitDF.shape[0] == 0:
                    print "no good fits found! Moving on!!"
                    continue
                # To this DF add a datetime column, to distinguish between fits
                currfitDF["date"] = currDate
                fitDFList.append( currfitDF )
                fitDF = pandas.concat( fitDFList )
            # Now append fitDF to a file and delete the DF!
            # Now we need date and time seperately for idl
            fitDF["dtStr"] = [ x.strftime("%Y%m%d") for x in fitDF["date"]]
            fitDF["tmStr"] = [ x.strftime("%H%M") for x in fitDF["date"]]
            # select the columns to save
            fitDF = fitDF[ ["normMLT", "MLAT", "vSaps", "azim",\
                 "vMagnErr", "azimErr", "dtStr", "tmStr"] ]
            # Now only update the file if fitDF is populated
            if fitDF is not None:
                with open(fitResFile, 'a') as fra:
                    fitDF.to_csv(fra, header=False,\
                                      index=False, sep=' ' )
            print "--------------------SAVED DATA------------------"
            print "--------------------NEXT EVENT------------------"
            del fitDF