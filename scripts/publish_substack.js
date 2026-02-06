const fs = require('fs');
const path = require('path');
const https = require('https');

const SUBSTACK_DOMAIN = 'saminthansivaji.substack.com';

function readJson(filePath) {
  const raw = fs.readFileSync(filePath, 'utf8');
  return JSON.parse(raw);
}

function jsonToMarkdown(post) {
  // For now, just use content as-is.
  // Later you can expand this to support sections, headings, etc.
  return post.content;
}

function publishToSubstack(post, sessionCookie) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({
      title: post.title,
      body_markdown: jsonToMarkdown(post),
      tags: post.tags || [],
      publish: true
    });

    const options = {
      hostname: SUBSTACK_DOMAIN,
      path: '/api/v1/posts',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data),
        'Cookie': `substack.sid=${sessionCookie}`,
        'User-Agent': 'githubinflow-substack-bot'
      }
    };

    const req = https.request(options, res => {
      let body = '';
      res.on('data', chunk => (body += chunk));
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          console.log('Substack response:', body);
          resolve(body);
        } else {
          console.error('Failed with status:', res.statusCode, body);
          reject(new Error(`Substack API error: ${res.statusCode}`));
        }
      });
    });

    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

async function main() {
  const filePath = process.argv[2];
  if (!filePath) {
    console.error('No file path provided.');
    process.exit(1);
  }

  const sessionCookie = process.env.SUBSTACK_SESSION;
  if (!sessionCookie) {
    console.error('SUBSTACK_SESSION not set.');
    process.exit(1);
  }

  const absolutePath = path.resolve(filePath);
  console.log('Reading post from:', absolutePath);

  const post = readJson(absolutePath);

  if (post.status !== 'ready') {
    console.log('Post is not marked as ready. Skipping.');
    process.exit(0);
  }

  try {
    await publishToSubstack(post, sessionCookie);
    console.log('Post published successfully.');

    // Move file to processed
    const processedDir = path.join(path.dirname(path.dirname(absolutePath)), 'processed');
    if (!fs.existsSync(processedDir)) {
      fs.mkdirSync(processedDir, { recursive: true });
    }

    const fileName = path.basename(absolutePath);
    const newPath = path.join(processedDir, fileName);

    fs.renameSync(absolutePath, newPath);
    console.log('Moved file to:', newPath);
  } catch (err) {
    console.error('Error publishing to Substack:', err);
    process.exit(1);
  }
}

main();
