var fs = require("fs");
var path = require("path");
var ffmetadata = require("ffmetadata");
var moment = require("moment");
//const MEDIA_DIR = "/Users/john/dev/js/radio/Radio/media";
const DIR_SEPARATOR = "/";
const MEDIA_DIR = "/Users/john/dev/js/radio/Radio/media";
const SHOW_NAME = "Radcliffe_and_Maconie";
const DATE_FORMAT = "YYYY-MM-DD";
const LEGACY_DATE_FORMAT = "DD_MM_YYYY";
const LEGACY_DATE_ONLY_EPISODE_TITLE_FORMAT = "DD/MM/YYYY";

// const SHOW_NAME = "The_Peoples_Songs";
// const SHOW_NAME = "The_Matter_of_the_North";


function isEpisodeTitleLegacyDateOnly(episodeTitle, broadcastDate) {
    return (episodeTitle === broadcastDate.format(LEGACY_DATE_ONLY_EPISODE_TITLE_FORMAT));
}

function updateEpisodeMetaData(fileDetails, data) {
    var episodeTitle = data.title;
    console.log("        Would update title to %s", episodeTitle);
    ffmetadata.write(fileDetails.fullPath, data, function(err, data) {
        if (err) console.error("Error writing metadata", err);
        else {
            console.log("File updated with title %s", episodeTitle);
        }
    });
}

function fileNameBeginsWith(file, beginning) {
    return (file.substr(0, beginning.length) === beginning);
}

function checkAndUpdateFileName(fileDetails, beginning, newBeginning, broadcastDate) {
    var fileEnding = fileDetails.file.substr(beginning.length);
    console.log("File ending: %s", fileEnding);
    var newFileName = newBeginning;
    if (fileEnding.substr(0, DATE_FORMAT.length) === broadcastDate.format(DATE_FORMAT)) {
        newFileName = newFileName.concat(fileEnding);
    } else if (fileEnding.substr(0, LEGACY_DATE_FORMAT.length) === broadcastDate.format(LEGACY_DATE_FORMAT)) {
        newFileName = newFileName.concat(broadcastDate.format(DATE_FORMAT), fileEnding.substr(LEGACY_DATE_FORMAT.length));
    } else {
        newFileName = newFileName.concat(broadcastDate.format(DATE_FORMAT), "_", fileEnding);
    }

    if (fileDetails.file !== newFileName) {
        console.log("New filename will be: %s", newFileName);
    } else {
        console.log("No rename required");
    }
}

function updateEpisodeFileName(fileDetails, broadcastDate) {
    var oldTypeFileNameBeginning = SHOW_NAME.concat("-");
    var newTypeFileNameBeginning = SHOW_NAME.concat("_-_");
    if (fileNameBeginsWith(fileDetails.file, oldTypeFileNameBeginning)) {
        checkAndUpdateFileName(fileDetails, oldTypeFileNameBeginning, newTypeFileNameBeginning, broadcastDate);
    } else if (fileNameBeginsWith(fileDetails.file, newTypeFileNameBeginning)) {
        checkAndUpdateFileName(fileDetails, newTypeFileNameBeginning, newTypeFileNameBeginning, broadcastDate);
    }
}

function readAndUpdateEpisodeFile(fileDetails) {
    ffmetadata.read(fileDetails.fullPath, function (err, data) {
        if (err) console.error("    ERROR READING METADATA", err);
        else {
            var episodeTitle = data.title;
            var broadcastDate = moment(data.date.substr(0, DATE_FORMAT.length), DATE_FORMAT);
            var updateTitle = false;
            console.log("    Title: %s", episodeTitle);
            console.log("    Broadcast date: %s", broadcastDate.format(DATE_FORMAT));

            if (!episodeTitle || isEpisodeTitleLegacyDateOnly(episodeTitle, broadcastDate)) {
                episodeTitle = broadcastDate.format(DATE_FORMAT);
                updateTitle = true;
            } else if (episodeTitle.substr(0, 10) != broadcastDate.format(DATE_FORMAT)) {
                episodeTitle = broadcastDate.format(DATE_FORMAT) + " - " + episodeTitle;
                updateTitle = true;
            }

            if (updateTitle) {
                data.title = episodeTitle;
                updateEpisodeMetaData(fileDetails, data);
                updateEpisodeFileName(fileDetails, broadcastDate);
            } else {
                console.log("        Leaving alone");
            }
        }
    });
}

function readDirectoryAndProcessFiles(dir) {
    fs.readdir( dir, function( err, files ) {
        if( err ) {
            console.error( "Could not list the directory.", err );
            process.exit( 1 );
        }

        files
            .filter(function(file) { return file.substr(-4) === '.mp3'; })
            .forEach( function( file, index ) {
                var fileDetails = {
                    dir: dir,
                    file: file,
                    fullPath: path.join(dir, file)
                };

                fs.stat( fileDetails.fullPath, function( error, stat ) {
                    if( error ) {
                        console.error( "Error stating file.", error );
                        return;
                    }

                    if( stat.isFile() ) {
                        console.log( "Processing file: %s", fileDetails.fullPath );
                        readAndUpdateEpisodeFile(fileDetails);
                    }
                } );
            } );
    } );
}

// readDirectoryAndProcessFiles(path.join(MEDIA_DIR, SHOW_NAME + "_TEST"));

readAndUpdateEpisodeFile({
    dir: "/Users/john/dev/js/radio/Radio/media/Radcliffe_and_Maconie_TEST",
    file: "Radcliffe_and_Maconie-2015-12-09-Bryan_Ferry-b06qnl6l.mp3",
    fullPath: "/Users/john/dev/js/radio/Radio/media/Radcliffe_and_Maconie_TEST/Radcliffe_and_Maconie-2015-12-09-Bryan_Ferry-b06qnl6l.mp3"
});