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

function updateEpisodeMetaData(fullPath, data) {
    var episodeTitle = data.title;
    console.log("        Would update title to %s", episodeTitle);
    ffmetadata.write(fullPath, data, function(err, data) {
        if (err) console.error("Error writing metadata", err);
        else {
            console.log("File updated with title %s", episodeTitle);
        }
    });
}

function fileNameBeginsWith(file, beginning) {
    return (file.substr(0, beginning.length) === beginning);
}

function checkAndUpdateFileName(showDir, file, beginning, newBeginning, broadcastDate) {
    var fileEnding = file.substr(beginning.length);
    console.log("File ending: %s", fileEnding);
    var newFileName = newBeginning;
    if (fileEnding.substr(0, DATE_FORMAT.length) === broadcastDate.format(DATE_FORMAT)) {
        newFileName = newFileName.concat(fileEnding);
    } else if (fileEnding.substr(0, LEGACY_DATE_FORMAT.length) === broadcastDate.format(LEGACY_DATE_FORMAT)) {
        newFileName = newFileName.concat(broadcastDate.format(DATE_FORMAT), fileEnding.substr(LEGACY_DATE_FORMAT.length));
    } else {
        newFileName = newFileName.concat(broadcastDate.format(DATE_FORMAT), "_", fileEnding);
    }

    if (file !== newFileName) {
       console.log("New filename will be: %s", newFileName);
    } else {
        console.log("No rename required");
    }
}

function updateEpisodeFileName(showDir, file, broadcastDate) {
    var oldTypeFileNameBeginning = SHOW_NAME.concat("-");
    var newTypeFileNameBeginning = SHOW_NAME.concat("_-_");
    if (fileNameBeginsWith(file, oldTypeFileNameBeginning)) {
        checkAndUpdateFileName(showDir, file, oldTypeFileNameBeginning, newTypeFileNameBeginning, broadcastDate);
    } else if (fileNameBeginsWith(file, newTypeFileNameBeginning)) {
        checkAndUpdateFileName(showDir, file, newTypeFileNameBeginning, newTypeFileNameBeginning, broadcastDate);
    }
}

function readAndUpdateEpisodeFile(showDir, file, fullPath) {
    ffmetadata.read(fullPath, function (err, data) {
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
            } else if (episodeTitle.substr(0, 10) != broadcastDate) {
                episodeTitle = broadcastDate.format(DATE_FORMAT) + " - " + episodeTitle;
                updateTitle = true;
            }

            if (updateTitle) {
                data.title = episodeTitle;
                updateEpisodeMetaData(fullPath, data);
                updateEpisodeFileName(showDir, file, broadcastDate);
            } else {
                console.log("        Leaving alone");
            }
        }
    });
}

var showDir = path.join(MEDIA_DIR, SHOW_NAME + "_TEST");
fs.readdir( showDir, function( err, files ) {
    if( err ) {
        console.error( "Could not list the directory.", err );
        process.exit( 1 );
    }

    files
        .filter(function(file) { return file.substr(-4) === '.mp3'; })
        .forEach( function( file, index ) {
            var fullPath = path.join( showDir, file );

            fs.stat( fullPath, function( error, stat ) {
            if( error ) {
                console.error( "Error stating file.", error );
                return;
            }

            if( stat.isFile() ) {
                console.log( "Processing file: %s", fullPath );
                readAndUpdateEpisodeFile(showDir, file, fullPath);
            }
        } );
    } );
} );
