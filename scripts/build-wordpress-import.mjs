import { mkdir, readFile, writeFile } from 'node:fs/promises'
import path from 'node:path'

const articlesDir = path.resolve(process.env.ARTICLES_DIR ?? path.join(process.cwd(), '..', '..', '..', '文章提取结果'))
const outputDir = path.join(process.cwd(), 'artifacts')
const outputFile = path.join(outputDir, 'wordpress-import.xml')
const index = JSON.parse(await readFile(path.join(articlesDir, 'index.json'), 'utf8'))

const dateOverrides = {
  17: '2026-05-15',
  36: '2025-11-20',
  37: '2025-12-07',
}

function parseDate(entry, content) {
  const raw = dateOverrides[entry.Number]
    ?? content.match(/(20\d{2})[.．]\s*(\d{1,2})[.．]\s*(\d{1,2})/)?.slice(1).join('-')
  if (!raw) throw new Error(`Missing date for article ${entry.Number}`)
  const [year, month, day] = raw.split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day, 12))
}

function escapeXml(value) {
  return value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;')
}

function cdata(value) {
  return `<![CDATA[${value.replaceAll(']]>', ']]]]><![CDATA[>')}]]>`
}

function articleBody(content) {
  return content
    .replace(/^# Article \d+\s*/u, '')
    .replace(/\n---\s*\n\s*Source:[\s\S]*$/u, '')
    .replace(/\n?20\d{2}[.．]\s*\d{1,2}[.．]\s*\d{1,2}\s*$/u, '')
    .trim()
}

function toHtml(body) {
  return body.split(/\r?\n/).map(line => line.trim()).filter(Boolean).map(line => `<p>${escapeXml(line)}</p>`).join('\n')
}

const items = []
for (const entry of index) {
  const content = await readFile(path.join(articlesDir, entry.File), 'utf8')
  const body = articleBody(content)
  const html = toHtml(body)
  const date = parseDate(entry, content)
  const mysqlDate = date.toISOString().slice(0, 19).replace('T', ' ')
  const slug = `article-${String(entry.Number).padStart(2, '0')}`
  const description = body.replace(/\s+/g, ' ').slice(0, 180)

  items.push(`
    <item>
      <title>${escapeXml(entry.FirstLine)}</title>
      <link>http://43.132.148.205/${slug}/</link>
      <pubDate>${date.toUTCString()}</pubDate>
      <dc:creator>${cdata('lanran')}</dc:creator>
      <guid isPermaLink="false">http://43.132.148.205/?p=${1000 + entry.Number}</guid>
      <description></description>
      <content:encoded>${cdata(html)}</content:encoded>
      <excerpt:encoded>${cdata(description)}</excerpt:encoded>
      <wp:post_id>${1000 + entry.Number}</wp:post_id>
      <wp:post_date>${cdata(mysqlDate)}</wp:post_date>
      <wp:post_date_gmt>${cdata(mysqlDate)}</wp:post_date_gmt>
      <wp:comment_status>${cdata('closed')}</wp:comment_status>
      <wp:ping_status>${cdata('closed')}</wp:ping_status>
      <wp:post_name>${cdata(slug)}</wp:post_name>
      <wp:status>${cdata('publish')}</wp:status>
      <wp:post_parent>0</wp:post_parent>
      <wp:menu_order>${entry.Number}</wp:menu_order>
      <wp:post_type>${cdata('post')}</wp:post_type>
      <wp:post_password></wp:post_password>
      <wp:is_sticky>0</wp:is_sticky>
      <category domain="category" nicename="forty-fifth-sunset">${cdata('第四十五次日落')}</category>
    </item>`)
}

const xml = `<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0"
  xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:wfw="http://wellformedweb.org/CommentAPI/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:wp="http://wordpress.org/export/1.2/">
  <channel>
    <title>The forty-fifth sunset</title>
    <link>http://43.132.148.205</link>
    <description></description>
    <pubDate>${new Date().toUTCString()}</pubDate>
    <language>zh-CN</language>
    <wp:wxr_version>1.2</wp:wxr_version>
    <wp:base_site_url>http://43.132.148.205</wp:base_site_url>
    <wp:base_blog_url>http://43.132.148.205</wp:base_blog_url>
    <wp:author>
      <wp:author_id>1</wp:author_id>
      <wp:author_login>${cdata('lanran')}</wp:author_login>
      <wp:author_email>${cdata('')}</wp:author_email>
      <wp:author_display_name>${cdata('lanran')}</wp:author_display_name>
      <wp:author_first_name>${cdata('')}</wp:author_first_name>
      <wp:author_last_name>${cdata('')}</wp:author_last_name>
    </wp:author>
    <wp:category>
      <wp:term_id>2</wp:term_id>
      <wp:category_nicename>${cdata('forty-fifth-sunset')}</wp:category_nicename>
      <wp:category_parent>${cdata('')}</wp:category_parent>
      <wp:cat_name>${cdata('第四十五次日落')}</wp:cat_name>
    </wp:category>${items.join('')}
  </channel>
</rss>
`

await mkdir(outputDir, { recursive: true })
await writeFile(outputFile, xml, 'utf8')
console.log(`Created ${outputFile} with ${items.length} posts`)
