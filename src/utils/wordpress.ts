import sanitizeHtml from 'sanitize-html'

const baseUrl = (import.meta.env.PUBLIC_WORDPRESS_URL || 'http://43.132.148.205').replace(/\/$/, '')

export interface WordPressTerm {
  id: number
  name: string
  slug: string
  taxonomy: string
}

export interface WordPressImage {
  src: string
  alt: string
  width?: number
  height?: number
}

export interface WordPressPost {
  id: number
  route: string
  slug: string
  title: string
  date: string
  modified: string
  excerpt: string
  content: string
  categories: WordPressTerm[]
  image?: WordPressImage
}

export interface WordPressCollection {
  slug: string
  title: string
  description: string
  posts: WordPressPost[]
}

const allowedTags = sanitizeHtml.defaults.allowedTags.concat(['img', 'figure', 'figcaption', 'audio', 'source'])
const allowedAttributes = {
  ...sanitizeHtml.defaults.allowedAttributes,
  img: ['src', 'alt', 'width', 'height', 'loading', 'decoding', 'class'],
  audio: ['controls', 'loop', 'preload', 'class'],
  source: ['src', 'type'],
}

function cleanHtml(value: string) {
  return sanitizeHtml(value, { allowedTags, allowedAttributes })
}

function stripHtml(value: string) {
  return sanitizeHtml(value, { allowedTags: [], allowedAttributes: {} }).trim()
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${baseUrl}/wp-json/wp/v2/${path}`)
  if (!response.ok) {
    throw new Error(`WordPress request failed (${response.status}): ${path}`)
  }
  return response.json() as Promise<T>
}

interface ApiPost {
  id: number
  slug: string
  date: string
  modified: string
  title: { rendered: string }
  excerpt: { rendered: string }
  content: { rendered: string }
  _embedded?: {
    'wp:featuredmedia'?: Array<{ source_url?: string; alt_text?: string; media_details?: { width?: number; height?: number } }>
    'wp:term'?: WordPressTerm[][]
  }
}

function normalizePost(post: ApiPost): WordPressPost {
  const media = post._embedded?.['wp:featuredmedia']?.[0]
  const categories = (post._embedded?.['wp:term'] ?? []).flat().filter(term => term.taxonomy === 'category')
  return {
    id: post.id,
    route: String(post.id),
    slug: post.slug,
    title: stripHtml(post.title.rendered),
    date: post.date,
    modified: post.modified,
    excerpt: stripHtml(post.excerpt.rendered),
    content: cleanHtml(post.content.rendered),
    categories,
    image: media?.source_url ? {
      src: media.source_url,
      alt: media.alt_text || stripHtml(post.title.rendered),
      width: media.media_details?.width,
      height: media.media_details?.height,
    } : undefined,
  }
}

export async function getWordPressPosts(): Promise<WordPressPost[]> {
  const posts = await fetchJson<ApiPost[]>('posts?per_page=100&orderby=date&order=desc&_embed')
  return posts.map(normalizePost)
}

export async function getWordPressPost(route: string) {
  if (/^\d+$/.test(route)) {
    return normalizePost(await fetchJson<ApiPost>(`posts/${route}?_embed`))
  }
  const posts = await fetchJson<ApiPost[]>(`posts?slug=${encodeURIComponent(route)}&_embed`)
  return posts[0] ? normalizePost(posts[0]) : null
}

export async function getWordPressPostPaths() {
  const posts = await getWordPressPosts()
  return posts.map(post => ({ slug: post.route }))
}

function hasCategory(post: WordPressPost, slugs: string[]) {
  return post.categories.some(category => slugs.includes(category.slug))
}

export async function getWordPressCollections(): Promise<WordPressCollection[]> {
  const posts = await getWordPressPosts()
  const collectionPosts = posts
    .filter(post => hasCategory(post, ['forty-fifth-sunset', 'di-si-wu-ci-ri-luo', '第四十五次日落']))
    .sort((a, b) => a.id - b.id)
  return collectionPosts.length > 0 ? [{
    slug: 'forty-fifth-sunset',
    title: '第四十五次日落',
    description: '一组关于时间、成长与记忆的文字。',
    posts: collectionPosts,
  }] : []
}

export async function getWordPressCollection(slug: string) {
  const collections = await getWordPressCollections()
  return collections.find(collection => collection.slug === slug) ?? null
}

export async function getWordPressGalleries(): Promise<WordPressPost[]> {
  const posts = await getWordPressPosts()
  return posts.filter(post => hasCategory(post, ['photography', 'photo', 'she-ying', '摄影集']))
}

export async function getWordPressGallery(slug: string) {
  const galleries = await getWordPressGalleries()
  return galleries.find(gallery => gallery.route === slug || gallery.slug === slug) ?? null
}

export function isCollectionPost(post: WordPressPost) {
  return hasCategory(post, ['forty-fifth-sunset', 'di-si-wu-ci-ri-luo', '第四十五次日落'])
}

export function isGalleryPost(post: WordPressPost) {
  return hasCategory(post, ['photography', 'photo', 'she-ying', '摄影集'])
}
