import { createServer } from 'node:http'
import { readFile, stat } from 'node:fs/promises'
import { extname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const DIST = resolve(fileURLToPath(new URL('./dist', import.meta.url)))
const PORT = process.env.PORT || 3000
// Runtime backend URL (used for the allowed-domains lookup).
const BACKEND_URL =
  process.env.API_URL || process.env.VITE_API_URL || 'http://127.0.0.1:8000'

const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
}

// Same rules as vite.config.js: empty list = allow all, error = fail closed.
async function buildFrameAncestors() {
  try {
    const response = await fetch(`${BACKEND_URL}/widget/domains`, {
      signal: AbortSignal.timeout(3000),
    })
    if (!response.ok) throw new Error()
    const { domains } = await response.json()
    if (!domains.length) return null
    return `frame-ancestors 'self' ${domains.join(' ')}`
  } catch {
    return "frame-ancestors 'self'"
  }
}

async function findFile(pathname) {
  let decoded
  try {
    decoded = decodeURIComponent(pathname)
  } catch {
    return null
  }
  const filePath = join(DIST, decoded)
  if (!filePath.startsWith(DIST)) return null // blocks ../ traversal
  try {
    if ((await stat(filePath)).isFile()) return filePath
  } catch {
    // fall through
  }
  return null
}

const server = createServer(async (req, res) => {
  const pathname = (req.url || '/').split('?')[0]

  let filePath = await findFile(pathname)
  if (!filePath) {
    // Missing file with an extension = real 404. Otherwise it's an app route.
    if (extname(pathname)) {
      res.writeHead(404).end('Not found')
      return
    }
    filePath = join(DIST, 'index.html')
  }

  const headers = {
    'Content-Type': TYPES[extname(filePath)] || 'application/octet-stream',
  }

  if (pathname.startsWith('/assets/')) {
    headers['Cache-Control'] = 'public, max-age=31536000, immutable'
  } else {
    // index.html and widget.js must always be fresh.
    headers['Cache-Control'] = 'no-cache'
  }

  if (pathname === '/chat' || pathname.startsWith('/chat/')) {
    const policy = await buildFrameAncestors()
    if (policy) headers['Content-Security-Policy'] = policy
  }

  try {
    const body = await readFile(filePath)
    res.writeHead(200, headers).end(body)
  } catch {
    res.writeHead(500).end('Server error')
  }
})

server.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend listening on ${PORT}, backend ${BACKEND_URL}`)
})