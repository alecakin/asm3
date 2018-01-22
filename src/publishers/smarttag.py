#!/usr/bin/python

import configuration
import i18n
import os
import sys
import utils

from base import FTPPublisher, get_microchip_data
from sitedefs import SMARTTAG_FTP_HOST, SMARTTAG_FTP_USER, SMARTTAG_FTP_PASSWORD

class SmartTagPublisher(FTPPublisher):
    """
    Handles publishing to SmartTag PETID
    """
    def __init__(self, dbo, publishCriteria):
        publishCriteria.uploadDirectly = True
        publishCriteria.thumbnails = False
        FTPPublisher.__init__(self, dbo, publishCriteria, 
            SMARTTAG_FTP_HOST, SMARTTAG_FTP_USER, SMARTTAG_FTP_PASSWORD)
        self.initLog("smarttag", "SmartTag Publisher")

    def stYesNo(self, condition):
        """
        Returns a CSV entry for yes or no based on the condition
        """
        if condition:
            return "\"Y\""
        else:
            return "\"N\""

    def run(self):
        
        if self.isPublisherExecuting(): return
        self.updatePublisherProgress(0)
        self.setLastError("")
        self.setStartPublishing()

        shelterid = configuration.smarttag_accountid(self.dbo)
        if shelterid == "":
            self.setLastError("No SmartTag Account id has been set.")
            self.cleanup()
            return

        animals = get_microchip_data(self.dbo, ["a.SmartTag = 1 AND a.SmartTagNumber <> ''", '90007400', '900141'], "smarttag")
        if len(animals) == 0:
            self.setLastError("No animals found to publish.")
            self.cleanup(save_log=False)
            return

        if not self.openFTPSocket(): 
            self.setLastError("Failed to open FTP socket.")
            if self.logSearch("530 Login") != -1:
                self.log("Found 530 Login incorrect: disabling SmartTag publisher.")
                configuration.publishers_enabled_disable(self.dbo, "st")
            self.cleanup()
            return

        # SmartTag want data files called shelterid_mmddyyyy_HHMMSS.csv in a folder
        # called shelterid_mmddyyyy_HHMMSS
        dateportion = i18n.format_date("%m%d%Y_%H%M%S", i18n.now(self.dbo.timezone))
        folder = "%s_%s" % (shelterid, dateportion)
        outputfile = "%s_%s.csv" % (shelterid, dateportion)
        self.mkdir(folder)
        self.chdir(folder)

        csv = []

        anCount = 0
        for an in animals:
            try:
                line = []
                anCount += 1
                self.log("Processing: %s: %s (%d of %d)" % ( an["SHELTERCODE"], an["ANIMALNAME"], anCount, len(animals)))
                self.updatePublisherProgress(self.getProgress(anCount, len(animals)))

                # If the user cancelled, stop now
                if self.shouldStopPublishing(): 
                    self.log("User cancelled publish. Stopping.")
                    self.resetPublisherProgress()
                    self.cleanup()
                    return

                # Upload one image for this animal with the name shelterid_animalid-1.jpg
                self.uploadImage(an, an["WEBSITEMEDIANAME"], "%s_%d-1.jpg" % (shelterid, an["ID"]))
                # accountid
                line.append("\"%s\"" % shelterid)
                # sourcesystem
                line.append("\"ASM\"")
                # sourcesystemanimalkey (corresponds to image name)
                line.append("\"%d\"" % an["ID"])
                # sourcesystemownerkey
                line.append("\"%s\"" % str(an["CURRENTOWNERID"]))
                # signupidassigned, signuptype
                if an["IDENTICHIPNUMBER"].startswith("90007400"):
                    # if we have a smarttag microchip number, use that instead of the tag
                    # since it's unlikely someone will want both
                    line.append("\"%s\"" % an["IDENTICHIPNUMBER"])
                    line.append("\"IDTAG-LIFETIME\"")
                else:
                    line.append("\"%s\"" % an["SMARTTAGNUMBER"])
                    sttype = "IDTAG-ANNUAL"
                    if an["SMARTTAGTYPE"] == 1: sttype = "IDTAG-5 YEAR"
                    if an["SMARTTAGTYPE"] == 2: sttype = "IDTAG-LIFETIME"
                    line.append("\"%s\"" % sttype)
                # signupeffectivedate
                line.append("\"" + i18n.python2display(self.locale, an["SMARTTAGDATE"]) + "\"")
                # signupbatchpostdt - only used by resending mechanism and we don't do that
                line.append("\"\"")
                # feecharged
                line.append("\"\"")
                # feecollected
                line.append("\"\"")
                # owner related stuff
                address = an["CURRENTOWNERADDRESS"]
                houseno = utils.address_house_number(address)
                streetname = utils.address_street_name(address)
                # ownerfname
                line.append("\"%s\"" % an["CURRENTOWNERFORENAMES"])
                # ownermname
                line.append("\"\"")
                #ownerlname
                line.append("\"%s\"" % an["CURRENTOWNERSURNAME"])
                # addressstreetnumber
                line.append("\"%s\"" % houseno)
                # addressstreetdir
                line.append("\"\"")
                # addressstreetname
                line.append("\"%s\"" % streetname)
                # addressstreettype
                line.append("\"\"")
                # addresscity
                line.append("\"%s\"" % an["CURRENTOWNERTOWN"])
                # addressstate
                line.append("\"%s\"" % an["CURRENTOWNERCOUNTY"])
                # addresspostal
                line.append("\"%s\"" % an["CURRENTOWNERPOSTCODE"])
                # addressctry
                line.append("\"USA\"")
                # owneremail
                line.append("\"%s\"" % an["CURRENTOWNEREMAILADDRESS"])
                # owneremail2
                line.append("\"\"")
                # owneremail3
                line.append("\"\"")
                # ownerhomephone
                line.append("\"%s\"" % an["CURRENTOWNERHOMETELEPHONE"])
                # ownerworkphone
                line.append("\"%s\"" % an["CURRENTOWNERWORKTELEPHONE"])
                # ownerthirdphone
                line.append("\"%s\"" % an["CURRENTOWNERMOBILETELEPHONE"])
                # petname
                line.append("\"%s\"" % an["ANIMALNAME"].replace("\"", "\"\""))
                # species
                line.append("\"%s\"" % an["SPECIESNAME"])
                # primarybreed
                line.append("\"%s\"" % an["BREEDNAME1"])
                # crossbreed (second breed)
                if an["CROSSBREED"] == 1:
                    line.append("\"%s\"" % an["BREEDNAME2"])
                else:
                    line.append("\"\"")
                # purebred
                line.append("\"%s\"" % self.stYesNo(an["CROSSBREED"] == 0))
                # gender
                line.append("\"%s\"" % an["SEXNAME"])
                # sterilized
                line.append("\"%s\"" % self.stYesNo(an["NEUTERED"] == 1))
                # primarycolor
                line.append("\"%s\"" % an["BASECOLOURNAME"])
                # secondcolor
                line.append("\"\"")
                # sizecategory
                line.append("\"%s\"" % an["SIZENAME"])
                # agecategory
                line.append("\"%s\"" % an["AGEGROUP"])
                # declawed
                line.append("\"%s\"" % self.stYesNo(an["DECLAWED"] == 1))
                # animalstatus (one of DECEASED, ADOPTED or NOT ADOPTED)
                if an["DECEASEDDATE"] is not None:
                    line.append("\"DECEASED\"")
                elif an["ACTIVEMOVEMENTTYPE"] == 1 and an["ACTIVEMOVEMENTDATE"] is not None:
                    line.append("\"ADOPTED\"")
                else:
                    line.append("\"NOT ADOPTED\"")
                # Add to our CSV file
                csv.append(",".join(line))
                # Mark success in the log
                self.logSuccess("Processed: %s: %s (%d of %d)" % ( an["SHELTERCODE"], an["ANIMALNAME"], anCount, len(animals)))
            except Exception as err:
                self.logError("Failed processing animal: %s, %s" % (str(an["SHELTERCODE"]), err), sys.exc_info())

        # Mark published
        self.markAnimalsPublished(animals)

        header = "accountid,sourcesystem,sourcesystemanimalkey," \
            "sourcesystemownerkey,signupidassigned,signuptype,signupeffectivedate," \
            "signupbatchpostdt,feecharged,feecollected,ownerfname,ownermname," \
            "ownerlname,addressstreetnumber,addressstreetdir,addressstreetname," \
            "addressstreettype,addresscity,addressstate,addresspostal,addressctry," \
            "owneremail,owneremail2,owneremail3,ownerhomephone,ownerworkphone," \
            "ownerthirdphone,petname,species,primarybreed,crossbreed,purebred,gender," \
            "sterilized,primarycolor,secondcolor,sizecategory,agecategory,declawed," \
            "animalstatus\n" 
        self.saveFile(os.path.join(self.publishDir, outputfile), header + "\n".join(csv))
        self.log("Uploading datafile %s" % outputfile)
        self.upload(outputfile)
        self.log("Uploaded %s" % outputfile)
        self.log("-- FILE DATA --")
        self.log(header + "\n".join(csv))
        self.cleanup()


