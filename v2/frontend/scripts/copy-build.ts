/**
 * Script to copy the built React app to the backend directory for serving
 */
import fs from 'fs-extra';
import path from 'path';

const source = path.join(__dirname, '..', 'build');
const destination = path.join(__dirname, '..', '..', 'backend', 'frontend_build');

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
