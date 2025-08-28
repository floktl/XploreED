const fs = require('fs');
const path = require('path');

// Function to recursively find all JS/TS files
function findFiles(dir, extensions = ['.js', '.jsx', '.ts', '.tsx']) {
    let results = [];
    const list = fs.readdirSync(dir);

    list.forEach(file => {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);

        if (stat && stat.isDirectory()) {
            results = results.concat(findFiles(filePath, extensions));
        } else if (extensions.some(ext => file.endsWith(ext))) {
            results.push(filePath);
        }
    });

    return results;
}

// Function to fix imports in a file
function fixImports(filePath) {
    let content = fs.readFileSync(filePath, 'utf8');
    let modified = false;

    // Fix Button imports
    if (content.includes('import { Button } from') && content.includes('common/UI/UI')) {
        content = content.replace(
            /import \{ Button(?:,\s*([^}]+))? \} from ['"]([^'"]*common\/UI\/UI[^'"]*)['"];?/g,
            (match, otherImports, importPath) => {
                modified = true;
                const relativePath = importPath.replace('common/UI/UI', 'common/UI/Button');
                if (otherImports) {
                    return `import Button from "${relativePath}";\nimport { ${otherImports} } from "${importPath}";`;
                } else {
                    return `import Button from "${relativePath}";`;
                }
            }
        );
    }

    // Fix Modal imports
    if (content.includes('import { Modal } from') && content.includes('common/UI/UI')) {
        content = content.replace(
            /import \{ Modal(?:,\s*([^}]+))? \} from ['"]([^'"]*common\/UI\/UI[^'"]*)['"];?/g,
            (match, otherImports, importPath) => {
                modified = true;
                const relativePath = importPath.replace('common/UI/UI', 'common/UI/Modal');
                if (otherImports) {
                    return `import Modal from "${relativePath}";\nimport { ${otherImports} } from "${importPath}";`;
                } else {
                    return `import Modal from "${relativePath}";`;
                }
            }
        );
    }

    // Fix Spinner imports
    if (content.includes('import { Spinner } from') && content.includes('common/UI/UI')) {
        content = content.replace(
            /import \{ Spinner(?:,\s*([^}]+))? \} from ['"]([^'"]*common\/UI\/UI[^'"]*)['"];?/g,
            (match, otherImports, importPath) => {
                modified = true;
                const relativePath = importPath.replace('common/UI/UI', 'common/UI/Spinner');
                if (otherImports) {
                    return `import Spinner from "${relativePath}";\nimport { ${otherImports} } from "${importPath}";`;
                } else {
                    return `import Spinner from "${relativePath}";`;
                }
            }
        );
    }

    // Fix Card imports
    if (content.includes('import { Card } from') && content.includes('common/UI/UI')) {
        content = content.replace(
            /import \{ Card(?:,\s*([^}]+))? \} from ['"]([^'"]*common\/UI\/UI[^'"]*)['"];?/g,
            (match, otherImports, importPath) => {
                modified = true;
                const relativePath = importPath.replace('common/UI/UI', 'common/UI/Card');
                if (otherImports) {
                    return `import Card from "${relativePath}";\nimport { ${otherImports} } from "${importPath}";`;
                } else {
                    return `import Card from "${relativePath}";`;
                }
            }
        );
    }

    if (modified) {
        fs.writeFileSync(filePath, content, 'utf8');
        console.log(`Fixed imports in: ${filePath}`);
    }
}

// Main execution
const srcDir = path.join(__dirname, 'src');
const files = findFiles(srcDir);

console.log(`Found ${files.length} files to check...`);

files.forEach(file => {
    try {
        fixImports(file);
    } catch (error) {
        console.error(`Error processing ${file}:`, error.message);
    }
});

console.log('Import fixing completed!');
