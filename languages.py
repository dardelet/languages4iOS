#!/usr/bin/env python
# coding: utf8

import os
import re
import sys
import binascii
import time
re.DOTALL = True

class ExportStringFile:

    languages = []
    sortedKeys = []

    #returns the list of the relevant (inside a .lproj directory) Localizable.String files in the project
    def getLocalizableStringsFile(self):
        stringFiles = []
        os.chdir("yoobiquity")
        dirs=os.listdir(".")
        for directory in dirs:
            if directory[-6:] == ".lproj":
                os.chdir(directory)
                if 'Localizable.strings' in os.listdir("."):
                    stringFiles.append(directory + '/Localizable.strings')
                os.chdir("..")
        return stringFiles

    #input: A line of a Localizable.String file. Example: "CREATE_ACCOUNT_PROGRESS_MESSAGE" = "We are registering you, please wait...";
    #output: {key: {language_key:value}}
    def parseLine(self, line, language):
        line = line.decode("utf8")
        try:
            m = re.search("\"[ ]*(.*?)[ ]*\"[ ]*=[ ]*\"(.*)\"[ ]*;?", line)
            key = m.group(1)
            if key not in self.sortedKeys:
                self.sortedKeys.append(key)
            value =  m.group(2)
        except AttributeError:
            print "Parsing error for line: " + line
        return {key:{language:value}}
        
    def getDictionnaryFromStringFile(self, filename):
        f = open(filename)
        language = re.search("(.*)\.lproj/.*", filename).group(1)
        language = "fr" if language == "Base" else language
        self.languages.append(language)
        dico = {}
        for line in f:
            if len(line) < 5:
                continue
            if line[0:2] == "//" or line[0:2] == "/*":
                continue
            dicoline = self.parseLine(line, language)
            dico.update(dicoline)
        f.close()
        return dico

    #Merges dictionnaries from different string files together
    def merge(self, a, b, path=None):
        if path is None: path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self.merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass # same leaf value
                else:
                    raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
            else:
                a[key] = b[key]
        return a


    def getDictionnaryFromProject(self):
        files = self.getLocalizableStringsFile()
        dico = {}
        for filename in files:
            dicofile = self.getDictionnaryFromStringFile(filename)
            self.merge(dico,dicofile)
        return dico

    def dictionnaryToCsv(self, dico):
        path = "../languages.csv"
        try:
            os.remove(path)
        except OSError:
            pass
        f = open(path, 'w')
        bitlist = ['EF', 'BB', 'BF']
        bytes = binascii.a2b_hex(''.join(bitlist))
        f.write(bytes)
        #Add title
        title = "Variable"
        for l in self.languages:
            title += ";" + l
        f.write(title+";END\n")
        for key in self.sortedKeys:
            line = "" 
            line += key + ";"
            for l in self.languages:
                if l in dico[key]:
                    line += dico[key][l] + ";"
                else:
                    line += ";"
            line = line + 'END\n'
            line = line.encode("utf8")
            f.write(line)
        f.close()

    def getCsv(self):
        self.dictionnaryToCsv(self.getDictionnaryFromProject())

class ImportCsv:

    languages = []
    sortedKeys = []
    dico = {}

    def parseLineIntoArray(self, line):
        line = line.decode("utf8")
        numberOfField = line.count(";")
        field = "(.*?);"
        regex = "".join([field for i in range(0, numberOfField)])+"END\n"
        fields = []
        try:
            m = re.search(regex, line)
            for i in range(1,numberOfField+1):
                fields.append(m.group(i))
            self.sortedKeys.append(fields[0])
        except AttributeError:
            print ("Parsing error for group " + str(i) + " at line: " + line).rstrip()
            quit()
        return fields

    def merge(self, a, b, path=None):
        if path is None: path = []
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self.merge(a[key], b[key], path + [str(key)])
                elif a[key] == b[key]:
                    pass # same leaf value
                else:
                    raise Exception('Conflict at %s' % '.'.join(path + [str(key)]))
            else:
                a[key] = b[key]
        return a

    def addArrayToDictionnary(self, array):
        dicoLine = {array[0]:{}}
        for language,translation in zip(self.languages,array[1:]):
            dicoLine[array[0]][language] = translation
        self.merge(self.dico,dicoLine) 

    def getDicoFromFile(self):
        f = open("languages.csv")
        firstLine = True
        for line in f:    
            array = self.parseLineIntoArray(line)
            if firstLine:
                self.languages = [unicode("Base") if i == "fr" else i for i in array[1:]]
                self.sortedKeys = self.sortedKeys[1:]
                firstLine = False
            else:
                self.addArrayToDictionnary(array)
        f.close()

    def writeFilesFromDico(self):
        for language in self.languages:
            self.writeFile(language)

    def writeFile(self, language):
        folderName = "yoobiquity/" + language + ".lproj"
        fileName = "Localizable.strings"
        tmpName = "/tmp/localizable"
        timeInMilliseconds = int(round(time.time() * 1000))
        try:
            os.chdir(folderName)
        except OSError:
            print "Couldn't find " + folderName + ". No such directory."
            quit()
        try:
            os.rename(fileName, fileName + ".old." + str(timeInMilliseconds))
            print "Creating copy of " + fileName + " in " + folderName
        except OSError:
            print "Couldn't find Localizable.strings. No such file."
            quit()
        f = open(tmpName, "w+")
        g = open(fileName, "w+")
        for key in self.sortedKeys:
            line = '"' + key + '" = "' + self.dico[key][language] + '";\n'
            line = line.encode("utf8")
            f.write(line)
        self.formatFile(f, g)
        f.close()
        g.close()
        os.remove(tmpName)
        os.chdir("../..")

    def formatFile(self, fileIn, fileOut):
        fileIn.seek(0)
        line = fileIn.readline()
        prefix1 = self.getPrefix(line)
        fileOut.write(line)
        for line in fileIn:
            prefix2 = self.getPrefix(line)
            if prefix1 != prefix2:
                fileOut.write("\n")
            prefix1 = prefix2
            fileOut.write(line)


    def getPrefix(self, line):
        try:
            m = re.search('"(.+?)[_"]', line)
            prefix = m.group(1)
        except AttributeError:
            print 'Prefix error'
            quit()
        return prefix

    def getStringFiles(self):
        self.getDicoFromFile()
        self.writeFilesFromDico()
                

if len(sys.argv) != 2:
    print "Usage: ./languages.py [import|export|update]"
else:
    if sys.argv[1] == "export":
        print "Creating csv file..."
        exportCommand = ExportStringFile()
        exportCommand.getCsv()
        print "Done. Check 'languages.csv'"
    elif sys.argv[1] == "import":
        print "Loading languages.csv file into String files..."
        importCommand = ImportCsv()
        importCommand.getStringFiles()
        print "Done"
    elif sys.argv[1] == "update":
        print "Loading new keys of Base file into the other language files"
        exportCommand = ExportStringFile()
        exportCommand.getCsv()
        os.chdir("..")
        importCommand = ImportCsv()
        importCommand.getStringFiles()
        print "Done"
    else:
        print "Not a valid command"
