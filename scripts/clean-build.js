#!/usr/bin/env node
/**
 * Cleanup script to remove Next.js internal files that Vercel might detect as serverless functions
 * This prevents errors when the project directory name contains spaces
 */
const fs = require('fs');
const path = require('path');

const filesToRemove = [
  '___next_launcher.cjs',
];

const dirsToCheck = [
  process.cwd(),
];

filesToRemove.forEach(file => {
  dirsToCheck.forEach(dir => {
    const filePath = path.join(dir, file);
    try {
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        console.log(`Removed: ${filePath}`);
      }
    } catch (error) {
      // Ignore errors - file might not exist or already removed
    }
  });
});
