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
  const cfClearance = process.env.SUBSTACK_CF_CLEARANCE;

  if (!sessionCookie) {
    console.error('SUBSTACK_SESSION not set.');
    process.exit(1);
  }

  if (!cfClearance) {
    console.error('SUBSTACK_CF_CLEARANCE not set.');
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
        },
        {
          name: 'cf_clearance',
          value: cfClearance,
          domain: 'saminthansivaji.substack.com',
          path: '/',
          httpOnly: false,
          secure: true
        }
      ],
      origins: []
    }
  });

  const page = await context.newPage();

  console.log('Opening Substack editor…');
  await page.goto('https://saminthansivaji.substack.com/publish/post', {
    waitUntil: 'domcontentloaded'
  });

  console.log('Waiting for redirect to editor with post ID…');
  await page.waitForURL(/\/publish\/post\/\d+/, { timeout: 60000 });

  console.log('Waiting for title field…');
  await page.waitForSelector('input[placeholder="Title"]', { timeout: 30000 });

  console.log('Typing title…');
  await page.fill('input[placeholder="Title"]', post.title);

  try {
    await page.fill('input[placeholder="Add a subtitle"]', post.subtitle || '');
  } catch (e) {
    console.log('Subtitle field not found (this is fine).');
  }

  console.log('Waiting for body editor…');
  await page.waitForSelector('div[contenteditable="true"]', { timeout: 30000 });

  console.log('Typing content…');
  await page.click('div[contenteditable="true"]');
  await page.keyboard.type(post.content, { delay: 5 });

  console.log('Clicking Continue…');
  await page.click('button:has-text("Continue")');

  console.log('Waiting for publish modal…');
  await page.waitForSelector('div[role="dialog"]', { timeout: 30000 });

  console.log('Clicking Send to everyone now…');
  await page.click('button:has-text("Send to everyone now")');

  console.log('Waiting for publish confirmation…');
  await page.waitForTimeout(8000);

  await browser.close();

  const processedDir = path.join(path.dirname(path.dirname(absolutePath)), 'processed');
  if (!fs.existsSync(processedDir)) {
    fs.mkdirSync(processedDir, { recursive: true });
  }

  const newPath = path.join(processedDir, path.basename(absolutePath));
  fs.renameSync(absolutePath, newPath);

  console.log('Post published and file moved to:', newPath);
}

main();
