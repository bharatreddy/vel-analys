if __name__ == "__main__":
    import lshell_opt
    import datetime
    inpLosVelFile = "/home/bharat/Documents/code/vel-analys/data/formatted-vels.txt"
    lsObj = lshell_opt.LshellFit(inpLosVelFile)
    inpDt = datetime.datetime( 2011, 4, 9, 8, 40 )
    lsObj.get_lshell_fits(inpDt)


class LshellFit(object):
    """
    A class to obtain SAPS velocities using 
    an optimized Lshell fitting method
    """
    def __init__(self, losdataFile):
        import pandas
        # get raw Los data from the input file and store it in a DF
        inpColNames = [ "dateStr", "timeStr", "beam", "range", \
          "azim", "Vlos", "MLAT", "MLON", "MLT", "radId", \
          "radCode"]
        self.velsDataDF = pandas.read_csv(losdataFile, sep=' ',\
                                     header=None, names=inpColNames)
        # add a datetime col
        self.velsDataDF["date"] = pandas.to_datetime( \
                                self.velsDataDF['dateStr'].astype(str) + "-" +\
                                self.velsDataDF['timeStr'].astype(str), \
                                format='%Y%m%d-%H%M')
        # for some reason MLAT is a str type, convert it to float
        self.velsDataDF["MLAT"] = self.velsDataDF["MLAT"].astype(float)
        # Also get a normMLT for plotting & analysis
        self.velsDataDF['normMLT'] = [x-24 if x >= 12\
             else x for x in self.velsDataDF['MLT']]

    def get_lshell_fits(self,dtObj):
        # given a date time obj, get the lshell fitted velocities.
        # First filter for SAPS velocities.
        self.filter_saps_vels()


    def filter_saps_vels(self):
        #### filter for SAPS velocities ####
        # remove velocies whose magnitude is less than 200 m/s
        self.velsDataDF = self.velsDataDF[ \
                abs(self.velsDataDF["Vlos"]) >= 200. ]
        # SAPS(westward) Vlos are positive for positive azimuths
        #  and vice versa. Filter the others out.
        self.velsDataDF = self.velsDataDF[ \
            self.velsDataDF["azim"]/self.velsDataDF["Vlos"] > 0.\
             ].reset_index(drop=True)
        print self.velsDataDF.head()
