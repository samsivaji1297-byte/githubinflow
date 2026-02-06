const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

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
  const post = JSON.parse(fs.readFileSync(absolutePath, 'utf8'));

  if (post.status !== 'ready') {
    console.log('Post is not marked as ready. Skipping.');
    process.exit(0);
  }

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    storageState: {
      cookies: [
        {
          name: 'substack.sid',
          value: sessionCookie,
          domain: 'saminthansivaji.substack.com',
          path: '/',
          httpOnly: true,
          secure: true
        }
      ],
      origins: []
    }
  });

  const page = await context.newPage();

  console.log('Opening Substack…');
  await page.goto('https://saminthansivaji.substack.com/publish/post');

  console.log('Waiting for editor…');
  await page.waitForSelector('[data-testid="editor"]', { timeout: 20000 });

  console.log('Typing title…');
  await page.fill('input[placeholder="Title"]', post.title);

  console.log('Typing content…');
  await page.click('[data-testid="editor"]');
  await page.keyboard.type(post.content, { delay: 5 });

  console.log('Clicking Publish…');
  await page.click('button:has-text("Publish")');

  console.log('Waiting for confirmation…');
  await page.waitForTimeout(5000);

  await browser.close();

  // Move file to processed
  const processedDir = path.join(path.dirname(path.dirname(absolutePath)), 'processed');
  if (!fs.existsSync(processedDir)) {
    fs.mkdirSync(processedDir, { recursive: true });
  }

  const newPath = path.join(processedDir, path.basename(absolutePath));
  fs.renameSync(absolutePath, newPath);

  console.log('Post published and file moved to:', newPath);
}

main();
