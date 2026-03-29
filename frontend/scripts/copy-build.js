/**
 * Script to copy the built React app to the backend directory for serving
 */
const fs = require('fs-extra');
const path = require('path');

const source = process.env.COPY_BUILD_SOURCE || path.join(__dirname, '..', 'dist');
const destination = process.env.COPY_BUILD_DESTINATION || path.join(__dirname, '..', '..', 'backend', 'frontend_build');

// Ensure destination directory exists
fs.ensureDirSync(destination);

// Copy files
try {
    fs.copySync(source, destination);
    console.log(`Successfully copied build files to ${destination}`);
} catch (err) {
    console.error(`Error copying build files: ${err}`);
    process.exit(1);
}

console.log('Build files have been copied to the backend directory!');
