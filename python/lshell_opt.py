if __name__ == "__main__":
    import lshell_opt
    import datetime
    inpLosVelFile = \
        "/home/bharat/Documents/code/vel-analys/data/formatted-vels.txt"
    inpSAPSDataFile = \
        "/home/bharat/Documents/code/vel-analys/data/processedSaps.txt"
    lsObj = lshell_opt.LshellFit(inpLosVelFile, inpSAPSDataFile=inpSAPSDataFile)
    inpDt = datetime.datetime( 2011, 4, 9, 8, 40 )
    resDF = lsObj.get_timewise_lshell_fits(inpDt)
    # plot the results
    plotFileName = \
        "/home/bharat/Documents/code/vel-analys/figs/lshell-test.pdf"
    lsObj.plot_lshell_results(resDF,plotFileName)


class LshellFit(object):
    """
    A class to obtain SAPS velocities using 
    an optimized Lshell fitting method
    """
    def __init__(self, losdataFile, inpSAPSDataFile=None):
        import pandas
        # get raw Los data from the input file and store it in a DF
        inpColNames = [ "dateStr", "timeStr", "beam", "range", \
          "azim", "Vlos", "MLAT", "MLON", "MLT", "radId", \
          "radCode"]
        self.velsDataDF = pandas.read_csv(losdataFile, sep=' ',\
                                     header=None, names=inpColNames)
        # add a datetime col
        # self.velsDataDF["date"] = pandas.to_datetime( \
        #                         self.velsDataDF['dateStr'].astype(str) + "-" +\
        #                         self.velsDataDF['timeStr'].astype(str), \
        #                         format='%Y%m%d-%H%M')
        self.velsDataDF["date"] = self.velsDataDF.apply( self.convert_to_datetime, axis=1 )
        # for some reason MLAT is a str type, convert it to float
        self.velsDataDF["MLAT"] = self.velsDataDF["MLAT"].astype(float)
        # Also get a normMLT for plotting & analysis
        self.velsDataDF['normMLT'] = [x-24 if x >= 12\
             else x for x in self.velsDataDF['MLT']]
        # We'll also need SAPS data file to determine
        # which velocities are below the auroral oval
        # This file location could be set to None if
        # all the velocities present in the velocity 
        # file are below the auroral oval!
        if inpSAPSDataFile is None:
            print "saps data file is set to None!"
            print "Assuming all vels are below auroral oval!!"
        self.inpSAPSDataFile = inpSAPSDataFile

    def convert_to_datetime(self,row):
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

    def convert_to_datetime_sapsDF(self,row):
        # Given a datestr and a time string convert to a python datetime obj.
        # For sapsDataDF. This is not a good thing but the columns
        # in the DF are named differently!
        import datetime
        datecolName="dateStr"
        timeColName="time"
        currDateStr = str( int( row[datecolName] ) )
    #     return currDateStr
        if int(row[timeColName]) < 10:
            currTimeStr = "000" + str( int( row[timeColName] ) )
        elif int(row[timeColName]) < 100:
            currTimeStr = "00" + str( int( row[timeColName] ) )
        elif int(row[timeColName]) < 1000:
            currTimeStr = "0" + str( int( row[timeColName] ) )
        else:
            currTimeStr = str( int( row[timeColName] ) )
        return datetime.datetime.strptime( currDateStr\
                        + ":" + currTimeStr, "%Y%m%d:%H%M" )

    def get_timewise_lshell_fits(self,selDateTime):
        import pandas
        # given a date time obj, get the lshell fitted velocities.
        # if the SAPS data file is not None, load the data in to 
        # a dataframe
        sapsDataDF = None
        if self.inpSAPSDataFile is not None:
            sapsDataDF = pandas.read_csv(self.inpSAPSDataFile, sep=' ',\
                     dtype={'dateStr':'str', 'time': 'str'})
            # sapsDataDF["date"] = pandas.to_datetime( \
            #                         sapsDataDF['dateStr'] + "-" +\
            #                         sapsDataDF['time'], format='%Y%m%d-%H%M')
            sapsDataDF["date"] = sapsDataDF.apply( self.convert_to_datetime_sapsDF, axis=1 )
        # Now filter for SAPS velocities based on time and AO bnd
        velAnlysDF = self.filter_saps_vels(selDateTime, sapsData=sapsDataDF)
        # Divide the velocities into cells. There are two types of cells/grid
        # that we use. A smaller grid and a bigger grid. The smaller grid is 
        # mainly used to search for best fit locations in the larger grid. The 
        # larger grid is then used to standardize the results across events.
        velAnlysDF = self.set_up_grids(velAnlysDF, smallGridMLT=0.5,\
             smallGridMLAT=0.25, largeGridMLT=1., largeGridMLAT=0.5)
        # Now check locations where we can get the best fits
        fitsDF = self.fit_sine_to_grids(velAnlysDF) 
        # seperate the results into two DFs
        # get all cells which are considered bad fits
        badFitDF = fitsDF[ fitsDF["vSaps"] == -1. ]
        # remove where fitting conditions failed, basically get good fits
        fitResultsDF = fitsDF[ ~fitsDF['fit_discarded'] \
            ].reset_index(drop=True)
        if fitResultsDF.shape[0] == 0:
            "print No good fit found!! Skipping.."
            return fitResultsDF
        # Also get only those rows where errors are < 50%
        fitResultsDF = fitResultsDF[ \
            (fitResultsDF["velMagnPercentError"] < 50.) &\
             (fitResultsDF["velAzimPercentError"] < 50.) ].reset_index()
        # Now finally use the good fits to standardize the results! Simply
        # use the azimuths from good fits to find velocities in cells nearby.
        lshellDF = self.expand_fit_results(velAnlysDF, fitResultsDF)
        return lshellDF

    def filter_saps_vels(self, selDateTime, sapsData=None):
        import numpy
        import pandas
        #### filter for SAPS velocities ####
        # remove velocies whose magnitude is less than 200 m/s
        self.velsDataDF = self.velsDataDF[ \
                abs(self.velsDataDF["Vlos"]) >= 150. ]
        # SAPS(westward) Vlos are positive for positive azimuths
        #  and vice versa. Filter the others out.
        self.velsDataDF = self.velsDataDF[ \
            self.velsDataDF["azim"]/self.velsDataDF["Vlos"] > 0.\
             ].reset_index(drop=True)
        # get velocities from the selected time only
        velAnlysDF = self.velsDataDF[ \
            self.velsDataDF["date"] == selDateTime ].reset_index(drop=True)
        velAnlysDF["normMLTRound"] = velAnlysDF["normMLT"].astype(int)
        if sapsData is not None:
            sapsSelPrdDF = sapsData[  ( sapsData["date"] - selDateTime < \
                numpy.timedelta64(30,'m') ) & ( sapsData["date"]\
                 - selDateTime >= numpy.timedelta64(0,'m') )  \
                ].reset_index(drop=True)
            # Now check if there is more than one time period in the 
            # selected interval ideally there shouldn't be, but if 
            # we find one we should do something about it 
            # (like take an average)...for now its undecided.!
            if len( sapsSelPrdDF["time"].unique() ) > 1:
                print "There is more than one time period selected!!!"
                print "NEED TO CHECK SOMETHING WRONG!!!"
                print "NEED TO CHECK SOMETHING WRONG!!!"
                print "NEED TO CHECK SOMETHING WRONG!!!"
            poesBndDF = sapsSelPrdDF[ ["poesMLT", "poesLat"] \
                                ].drop_duplicates().reset_index(drop=True)
            # Have a normalized MLT for ease of comparison
            poesBndDF['normMLT'] = [x-24 if x >= 12 else x \
                for x in poesBndDF['poesMLT']]
            # Merge POES boundary DF with the vels DF
            # print "shape before join--->", velAnlysDF.shape
            velAnlysDF = pandas.merge( velAnlysDF, poesBndDF, \
                left_on="normMLTRound", right_on="normMLT", how="inner" )
            # print "shape after join--->", velAnlysDF.shape
            # Filter out velocties above the POES boundary
            velAnlysDF = velAnlysDF[ \
                velAnlysDF["MLAT"] < velAnlysDF["poesLat"] \
                ].reset_index(drop=True).drop_duplicates()
            # print "shape after filtering by boundary--->", velAnlysDF.shape
        # Now return the velocity DF
        return velAnlysDF

    def set_up_grids(self, velAnlysDF, smallGridMLT=0.5,\
         smallGridMLAT=0.25, largeGridMLT=1., largeGridMLAT=0.5):
        # setup grids/cells both large and small for velocities
        # smaller grid for searching optimal locations!
        velAnlysDF["grid_MLT"] = [ \
            round(x*smallGridMLT**-1)/(smallGridMLT**-1)\
             for x in velAnlysDF['normMLT_x'] ]
        velAnlysDF["grid_MLAT"] = [ \
            round(x*smallGridMLAT**-1)/(smallGridMLAT**-1)\
             for x in velAnlysDF['MLAT'] ]
        velAnlysDF = velAnlysDF[ [ "beam", "range", "azim", "Vlos", "MLAT", \
                                  "MLT", "grid_MLT", "grid_MLAT", "radId", \
                                  "radCode", "normMLT_x" ] ]
        # Have a standard grid set up too!
        # This is to have a common grid for statistics
        velAnlysDF["std_grid_MLT"] = [ round(x*largeGridMLT**-1)/(largeGridMLT**-1) \
                        - largeGridMLT/2. for x in velAnlysDF['normMLT_x'] ]
        velAnlysDF["std_grid_MLAT"] = [ round(x*largeGridMLAT**-1)/(largeGridMLAT**-1) \
                        - largeGridMLAT/2. for x in velAnlysDF['MLAT'] ]
        return velAnlysDF

    def vel_sine_func(self, theta, Vmax, delTheta):
        import numpy
        # Fit a sine curve for a given cell
        # we are working in degrees but numpy deals with radians
        # convert to radians
        return Vmax * numpy.sin( numpy.deg2rad(theta) +\
                                numpy.deg2rad(delTheta) )

    def fit_sine_to_grids(self, velAnlysDF):
        import pandas
        import numpy
        import scipy.optimize
        # In this function we'll get fitting info about all 2x2 cells
        # We can then decide on which cells to choose!
        # get count of data points in each cell
        gridCounts = velAnlysDF.groupby(["grid_MLT", \
            "grid_MLAT"])["Vlos"].count()
        # Get max and min azim values
        azimMax = velAnlysDF.groupby(["grid_MLT", \
            "grid_MLAT"], sort=False)\
                     ['azim'].max()
        azimMin = velAnlysDF.groupby(["grid_MLT", \
            "grid_MLAT"], sort=False)\
                     ['azim'].min()
        azimMax.name = 'max_azim'
        azimMin.name = 'min_azim'
        gridCounts.name = 'count'
        gridDataDF = pandas.concat( [azimMax, azimMin, gridCounts],\
             axis=1 ).reset_index()
        # We'll store the fitting results in a DF
        gridMLTArr = []
        gridMLATArr = []
        gridMLTEndArr = []
        gridMLATEndArr = []
        vMaxArr = []
        azimArr = []
        vErrArr = []
        azimErrArr = []
        vLosMeanArr = []
        vLosMaxArr = []
        fitDiscardArr = []

        normMltVals = list( numpy.sort( gridDataDF["grid_MLT"].unique() ) )
        mlatVals = list( numpy.sort( gridDataDF["grid_MLAT"].unique() ) )
        # Loop using min/max MLT and MLAT to identify grids
        for inmlt in normMltVals:
            for jmlat in mlatVals:
                currVelCellDF = gridDataDF[ \
                                ( (gridDataDF["grid_MLT"] >= inmlt) &\
                                 (gridDataDF["grid_MLT"] <= inmlt+1.) &\
                                    (gridDataDF["grid_MLAT"] >= jmlat) &\
                                    (gridDataDF["grid_MLAT"] <= jmlat+0.5) )\
                                     ].reset_index(drop=True)
                # set this to true if any condition is not satisfied
                # and fitting fails!
                currFitFail = False
                # discard all the cells with one or less data points
                if currVelCellDF.shape[0] <= 2:
                    continue
                # check azim range!
                currCellAzimRange = currVelCellDF["max_azim"].max()\
                - currVelCellDF["min_azim"].min()
                # if azim range is less than 35 discard the cell!
                if abs(currCellAzimRange) < 35:
                    currFitFail = True
                # now check number of unique data points in azimuths!
                uniqAzims = set( list(currVelCellDF["max_azim"].unique())\
                                + list(currVelCellDF["min_azim"].unique()) )
                # skip data from the cells where number of readings if less
                # discard all the cells where uniq azimuths are less than 3!
                if len(uniqAzims) < 3:
                    currFitFail = True
                # If the fit failed condition is set! don't even bother fitting data
                # else verify sine curve fitting with the selected/remaining cells
                currVelDetDF = velAnlysDF[\
                         ( (velAnlysDF["grid_MLT"] >= inmlt) &\
                          (velAnlysDF["grid_MLT"] <= inmlt+1.) &\
                        (velAnlysDF["grid_MLAT"] >= jmlat) &\
                         (velAnlysDF["grid_MLAT"] <= jmlat+0.5) ) ].\
                                reset_index(drop=True)
                if not currFitFail:        
                    popt, pcov = scipy.optimize.curve_fit(self.vel_sine_func, \
                                            currVelDetDF['azim'].T,\
                                            currVelDetDF['Vlos'].T,
                                           p0=( 1000., 10. ))
                    # Now discard the bad fits, at this point we'll just use azimuths
                    # discard the estimated azimuths which don't fall in the -90 +/- 20 range
                    # We can further discard cells based on errors etc!
                    if abs( popt[1] ) > 20.:
                        currFitFail = True            
                gridMLTArr.append( inmlt )
                gridMLATArr.append( jmlat )
                gridMLTEndArr.append( inmlt + 1. )
                gridMLATEndArr.append( jmlat + 0.5 )
                fitDiscardArr.append(currFitFail)
                vLosMeanArr.append( currVelDetDF['Vlos'].mean() )
                if ( numpy.abs( numpy.min(currVelDetDF['Vlos']) )\
                     >= numpy.max( currVelDetDF['Vlos'] ) ):
                    currVlosMax = numpy.min(currVelDetDF['Vlos'])
                else:
                    currVlosMax = numpy.max(currVelDetDF['Vlos'])
                currVlosMaxAzim = currVelDetDF[ \
                    currVelDetDF['Vlos'] == currVlosMax ]["azim"].tolist()[0]
                vLosMaxArr.append( ( currVlosMax, currVlosMaxAzim ) )
                if not currFitFail:
                    vMaxArr.append( popt[0] )
                    azimArr.append( popt[1] )
                    vErrArr.append( pcov[0,0]**0.5 )
                    azimErrArr.append( pcov[1,1]**0.5 )
                else:
                    vMaxArr.append( -1. )
                    azimArr.append( -1. )
                    vErrArr.append( -1. )
                    azimErrArr.append( -1. )
                
        # convert to a dataframe
        fitResultsDF = pandas.DataFrame(
            {'grid_MLT_Begin': gridMLTArr,
             'grid_MLAT_Begin': gridMLATArr,
             'grid_MLT_End': gridMLTEndArr,
             'grid_MLAT_End': gridMLATEndArr,
             'vSaps': vMaxArr,
             'azim': azimArr,
             'vErr': vErrArr,
             'azimErr': azimErrArr,
             'vLosMean': vLosMeanArr,
             'vLosMax': vLosMaxArr,
             'fit_discarded' : fitDiscardArr
            })
        # get a MLT/MLAT grid
        fitResultsDF["grid_MLT"] = (fitResultsDF["grid_MLT_Begin"] +\
                                    fitResultsDF["grid_MLT_End"])/2.
        fitResultsDF["grid_MLAT"] = (fitResultsDF["grid_MLAT_Begin"] +\
                                    fitResultsDF["grid_MLAT_End"])/2.
        fitResultsDF['grid_normMLT'] = [x-24 if x >= 12 else x\
                                        for x in fitResultsDF['grid_MLT']]
        # calculate fit errors
        fitResultsDF["velMagnPercentError"] = abs( \
            fitResultsDF["vErr"]*100./fitResultsDF["vSaps"] )
        fitResultsDF["velAzimPercentError"] = abs( \
            fitResultsDF["azimErr"]*100./fitResultsDF["azim"] )
        return fitResultsDF

    def expand_fit_results(self, velAnlysDF, fitResultsDF):
        import pandas
        import numpy
        # Exapand fit results from good fit locations to locations
        # where good fits cannot be obtained! but los velocities 
        # found! These can be used to get results on a standard map!
        # In this section we need to get the results into a standard format
        # We'll choose a standard grid! and first get all the good fits into
        # the grid
        dataTupleArr = []

        stdPlotMLTs = numpy.sort( velAnlysDF['std_grid_MLT'].unique() ).tolist()
        stdPlotMLTs = stdPlotMLTs + [ max(stdPlotMLTs) + 1. ]
        stdPlotMLATs = numpy.sort( velAnlysDF['std_grid_MLAT'].unique() ).tolist()
        stdPlotMLATs = stdPlotMLATs + [ max(stdPlotMLATs) + 0.5 ]
        # lshell fit of cells with good fits!
        for crStdMLAT in stdPlotMLATs:
            for crStdMLT in stdPlotMLTs:
        #         print crStdMLAT, crStdMLT, " centered-->", crStdMLAT + 0.25, crStdMLT + 0.5
                slctdMLT = crStdMLT + 0.5
                slctdMLAT = crStdMLAT + 0.25
                # Now check if there are any good fits in the selected MLT/MLAT
                selDataDF = fitResultsDF[\
                     ( abs(fitResultsDF["grid_MLAT"] - slctdMLAT) <= 0.25 ) &\
                        ( abs(fitResultsDF["grid_MLT"] - slctdMLT) <= 0.5 )\
                        ].reset_index(drop=True)
                if selDataDF.shape[0] > 0:
                    # Now the important thing here is to deal with multiple values
                    # Its probably best to keep things simple (for now at least!).
                    # Just get the row with the lowest azim error (if there are multiple rows still)
                    # then for lowest vel magn error!
                    if selDataDF.shape[0] > 1 :
                        velSapsMean = selDataDF["vSaps"].mean()
                        velSapsStd = selDataDF["vSaps"].std()
                        azimSapsMean = selDataDF["azim"].mean()
                        azimSapsStd = selDataDF["azim"].std()
                        # get row(s) with lowest azim error
                        selDataDF = selDataDF[ selDataDF["velAzimPercentError"] == \
                                        selDataDF["velAzimPercentError"].min()\
                                        ].reset_index(drop=True)
                        # if we still have multiple rows, get the row with lowest 
                        # vel magn error!
                        if selDataDF.shape[0] > 1 :
                            selDataDF = selDataDF[\
                                 selDataDF["velMagnPercentError"] ==\
                                  selDataDF["velMagnPercentError"].min()\
                                  ].reset_index(drop=True)
                    selVelMagn = round( selDataDF["vSaps"].tolist()[0], 2 )
                    selVelAzim = round( selDataDF["azim"].tolist()[0], 2 )
                    selVelMagnErr = round( \
                        selDataDF["velMagnPercentError"].tolist()[0], 2 )
                    selVelAzimErr = round( \
                        selDataDF["velAzimPercentError"].tolist()[0], 2 )
                    selVlosMax = selDataDF["vLosMax"].tolist()[0]
                    selVlosMean = round( \
                        selDataDF["vLosMean"].tolist()[0], 2 )
                    # Populate the values
                    dataTupleArr.append( (slctdMLT, slctdMLAT, selVelMagn, \
                        selVelAzim, selVelMagnErr, selVelAzimErr, \
                        selVlosMean, selVlosMax, True) )

        # Now work on the cells with badFitting results
        for crStdMLAT in stdPlotMLATs:
            for crStdMLT in stdPlotMLTs:
                slctdMLT = crStdMLT + 0.5
                slctdMLAT = crStdMLAT + 0.25
                # Skip those values that are already present in goodfits
                skipCurrValue = False
                for dta in dataTupleArr:
                    if ( (abs(slctdMLT-dta[0]) < 0.1) & \
                        (abs(slctdMLAT-dta[1]) < 0.1) ):
                        skipCurrValue = True
                if skipCurrValue:
                    continue
                # We need velocity data for getting vLos and Azim in a given cell
                currVelDetDF = velAnlysDF[ ( (velAnlysDF["std_grid_MLT"] == crStdMLT) &\
                                            (velAnlysDF["std_grid_MLAT"] == crStdMLAT)  ) ].\
                                reset_index(drop=True)
                # If there are no values in currVelDetDF then skip
                if currVelDetDF.shape[0] == 0:
                    continue
                currCellMeanVLos = currVelDetDF['Vlos'].mean()
                if ( numpy.abs( numpy.min(currVelDetDF['Vlos']) ) >=\
                     numpy.max( currVelDetDF['Vlos'] ) ):
                    currVlosMax = numpy.min(currVelDetDF['Vlos'])
                else:
                    currVlosMax = numpy.max(currVelDetDF['Vlos'])
                currVlosMaxAzim = currVelDetDF[ currVelDetDF['Vlos'] == \
                    currVlosMax ]["azim"].tolist()[0]
                currCellVLosAzimMaxVal = ( currVlosMax, currVlosMaxAzim )                
                # Now check if there are any good fits close to the selected MLT/MLAT
                # Currently, we'll use +/- 1 hour MLT and 1 degrees MLAT
                selDataDF = fitResultsDF[ ( abs(fitResultsDF["grid_MLAT"] \
                                - slctdMLAT) <= 1. ) &\
                                ( abs(fitResultsDF["grid_MLT"] -\
                                 slctdMLT) <= 1. )].reset_index(drop=True)
                if ( selDataDF.shape[0] == 0 ):
                    continue
                # select closest location based on MLTs
                selDataDF["diff_MLT"] = selDataDF["grid_MLT"] - slctdMLT
                selDataDF["diff_MLAT"] = selDataDF["grid_MLAT"] - slctdMLAT
                minDiffMLT = selDataDF["diff_MLT"].abs().min()
                minDiffMlat = selDataDF["diff_MLAT"].abs().min()
                # Get the closest MLT first and then select the closest latitude
                if ( minDiffMLT == 0. ):
                    selDataDF = selDataDF[ \
                        selDataDF["diff_MLT"] == minDiffMLT \
                        ].reset_index(drop=True)
                    selDataDF = selDataDF[ ( selDataDF["diff_MLAT"] == \
                                        selDataDF["diff_MLAT"].abs().min() ) |\
                                        ( selDataDF["diff_MLAT"] == \
                                        -1*selDataDF["diff_MLAT"].abs().min() ) ]\
                                        .reset_index(drop=True)
                    # If we get only one value use it.
                    if selDataDF.shape[0] == 1:
                        nearestAzim = selDataDF["azim"].values[0]
                        # Now note for vLosMax which is used to estimate SAPS velocity
                        # We'll use the data from velAnlysDF! Because thats the actual
                        # l-o-s data measured in the cell! Same for vLostMean
                        nearestVlosMax = currCellVLosAzimMaxVal
                        nearestVlosMean = currCellMeanVLos
                        nearestAzimErr = selDataDF["velAzimPercentError"].values[0]
                        nearestVSapsErr = selDataDF["velMagnPercentError"].values[0]
                    # If we find multiple values choose the one with min error (PERCENT!!!) in azim
                    else:
                        selDataDF = selDataDF[ ( \
                            selDataDF["velAzimPercentError"] ==\
                             selDataDF["velAzimPercentError"].abs().min() ) |\
                                ( selDataDF["velAzimPercentError"] == \
                                -1*selDataDF["velAzimPercentError"].abs().min() ) ]
                        # Now if we find multiple values, just choose one
                        nearestAzim = selDataDF["azim"].values[0]
                        # Now note for vLosMax which is used to estimate SAPS velocity
                        # We'll use the data from velAnlysDF! Because thats the actual
                        # l-o-s data measured in the cell! Same for vLostMean
                        nearestVlosMax = currCellVLosAzimMaxVal
                        nearestVlosMean = currCellMeanVLos
                        nearestAzimErr = selDataDF["velAzimPercentError"].values[0]
                        nearestVSapsErr = selDataDF["velMagnPercentError"].values[0]
                else:
                    # Now we need to take care of +/- signs for MLTs as well
                    selDataDF = selDataDF[ ( selDataDF["diff_MLT"] == \
                                            selDataDF["diff_MLT"].abs().min() ) |\
                                            ( selDataDF["diff_MLT"] == \
                                            -1*selDataDF["diff_MLT"].abs().min() ) ]\
                                            .reset_index(drop=True)
                    # If we get only one value use it.
                    if selDataDF.shape[0] == 1:
                        nearestAzim = selDataDF["azim"].values[0]
                        # Now note for vLosMax which is used to estimate SAPS velocity
                        # We'll use the data from velAnlysDF! Because thats the actual
                        # l-o-s data measured in the cell! Same for vLostMean
                        nearestVlosMax = currCellVLosAzimMaxVal
                        nearestVlosMean = currCellMeanVLos
                        nearestAzimErr = selDataDF["velAzimPercentError"].values[0]
                        nearestVSapsErr = selDataDF["velMagnPercentError"].values[0]
                    else:
                        selDataDF = selDataDF[ ( selDataDF["diff_MLAT"] == \
                                            selDataDF["diff_MLAT"].abs().min() ) |\
                                            ( selDataDF["diff_MLAT"] == \
                                            -1*selDataDF["diff_MLAT"].abs().min() ) ]\
                                            .reset_index(drop=True)
                        # If we get only one value use it.
                        if selDataDF.shape[0] == 1:
                            nearestAzim = selDataDF["azim"].values[0]
                            # Now note for vLosMax which is used to estimate SAPS velocity
                            # We'll use the data from velAnlysDF! Because thats the actual
                            # l-o-s data measured in the cell! Same for vLostMean
                            nearestVlosMax = currCellVLosAzimMaxVal
                            nearestVlosMean = currCellMeanVLos
                            nearestAzimErr = selDataDF["velAzimPercentError"].values[0]
                            nearestVSapsErr = selDataDF["velMagnPercentError"].values[0]
                        # If we find multiple values choose the one with min error (PERCENT!!!) in azim
                        else:
                            selDataDF = selDataDF[ ( selDataDF["velAzimPercentError"] \
                                == selDataDF["velAzimPercentError"].abs().min() ) |\
                                    ( selDataDF["velAzimPercentError"] \
                                    == -1*selDataDF["velAzimPercentError"].abs().min() ) ]
                            # Now if we find multiple values, just choose one
                            nearestAzim = selDataDF["azim"].values[0]
                            # Now note for vLosMax which is used to estimate SAPS velocity
                            # We'll use the data from velAnlysDF! Because thats the actual
                            # l-o-s data measured in the cell! Same for vLostMean
                            nearestVlosMax = currCellVLosAzimMaxVal
                            nearestVlosMean = currCellMeanVLos
                            nearestAzimErr = selDataDF["velAzimPercentError"].values[0]
                            nearestVSapsErr = selDataDF["velMagnPercentError"].values[0]
                estSapsVel = nearestVlosMax[0]/( numpy.cos( \
                                            numpy.deg2rad( 90.-nearestAzim-nearestVlosMax[1] ) ) )
                # Populate the values 
                dataTupleArr.append( (slctdMLT, slctdMLAT, \
                            round(estSapsVel,2), round(nearestAzim,2),\
                             round(nearestVSapsErr,2), round(nearestAzimErr,2),\
                              round(nearestVlosMean,2), nearestVlosMax, False) )

        # Finally convert the values to a dataframe
        lshellDFColList = [ "normMLT", "MLAT", "vSaps", "azim",\
                         "vMagnErr", "azimErr", "vLosMean",\
                         "vLosMax", "goodFitCheck" ]
        lshellDF = pandas.DataFrame( dataTupleArr, columns=lshellDFColList )


        # Plotting end points of vectors
        lshellDF["plot_MLATEnd"] = numpy.round( \
            (lshellDF["vSaps"]/1000.) * \
            numpy.cos( numpy.deg2rad(-90-1*lshellDF["azim"]) )\
             + lshellDF["MLAT"], 2)
        lshellDF["plot_normMLTEnd"] = numpy.round( \
            (lshellDF["vSaps"]/1000.) * \
            numpy.sin( numpy.deg2rad(-90-1*lshellDF["azim"]) )\
             + lshellDF["normMLT"], 2)
        return lshellDF

    def plot_lshell_results(self,lshellDF,plotFileName):
        # plot the lshell results
        import seaborn as sns
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
        from matplotlib.colors import Normalize
        # Seaborn styling
        sns.set_style("darkgrid")
        sns.set_context("paper")
        seaMap = ListedColormap(sns.color_palette("Reds"))
        # Plot using matplotlib
        fig1 = plt.figure()
        ax = fig1.add_subplot(111)
        velScaleMin = 0.
        # round off max velocity to the next hundred
        velScaleMax = (lshellDF["vSaps"].max() + 100.)*100/100\
             - (lshellDF["vSaps"].max() + 100.)%100

        lshellDF.plot( kind='scatter',
                      x='normMLT',
                      y='MLAT',
                      c='vSaps',
                      s=1., cmap=seaMap, 
                      vmin=velScaleMin, vmax=velScaleMax, ax=ax)
        ax.set_ylabel("MLAT")
        ax.set_xlabel("MLT", fontsize=12)
        ax.set_title( "Velocities" )
        ax.set_ylim( [int(round(lshellDF['MLAT'].min()))-1, \
                      int(round(lshellDF['MLAT'].max()))+1] )
        ax.set_xlim( [int(round(lshellDF['plot_normMLTEnd'].min()))-1, \
                      int(round(lshellDF['plot_normMLTEnd'].max())) + 1] )
        plotMLTends = lshellDF['plot_normMLTEnd'].tolist()
        plotMLATends = lshellDF['plot_MLATEnd'].tolist()
        plotMLTbegins = lshellDF['normMLT'].tolist()
        plotMLATbegins = lshellDF['MLAT'].tolist()
        plotVelMagns = lshellDF['vSaps'].tolist()
        gfitTypeCheck = lshellDF['goodFitCheck'].tolist()
        # Normalize velocities according to colorbar
        colNorm = Normalize( vmin=velScaleMin, vmax=velScaleMax )
        for currMLTend, currMLATend, currMLTbgn, currMLATbgn,\
             currVel, gftChk in zip( plotMLTends, plotMLATends,\
              plotMLTbegins, plotMLATbegins, plotVelMagns, gfitTypeCheck ) :
                # get a appropriate color for each bar
                currCol = seaMap( colNorm(currVel) )
                if gftChk:
                    ax.plot( [currMLTbgn, currMLTend], \
                        [ currMLATbgn, currMLATend ], color=currCol )        
                    ax.arrow( currMLTbgn, currMLATbgn, currMLTend-currMLTbgn, \
                        currMLATend-currMLATbgn, head_width=0.1, \
                        head_length=0.2, fc=currCol, ec=currCol)
                else:            
                    ax.plot( [currMLTbgn, currMLTend], \
                        [ currMLATbgn, currMLATend ], \
                        color=currCol, linestyle='dotted' )
                    ax.arrow( currMLTbgn, currMLATbgn, \
                        currMLTend-currMLTbgn, currMLATend-currMLATbgn,\
                             head_width=0.1, head_length=0.2, fc=currCol,\
                              ec=currCol, linestyle='dotted')
        ax.get_figure().savefig(plotFileName,bbox_inches='tight')