import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

const BACKEND_URL = process.env.VITE_API_URL || 'http://127.0.0.1:8000'

// Sets Content-Security-Policy: frame-ancestors on /chat, using the
// allowed domains saved in the backend. Empty list = any site may embed.
async function buildFrameAncestors() {
  try {
    const response = await fetch(`${BACKEND_URL}/widget/domains`)
    if (!response.ok) throw new Error()
    const { domains } = await response.json()

    if (!domains.length) return null
    return `frame-ancestors 'self' ${domains.join(' ')}`
  } catch {
    // Backend unreachable: fail closed.
    return "frame-ancestors 'self'"
  }
}

function frameAncestorsPlugin() {
  const middleware = async (req, res, next) => {
    const pathname = (req.url || '').split('?')[0]

    if (pathname === '/chat' || pathname.startsWith('/chat/')) {
      const policy = await buildFrameAncestors()
      if (policy) res.setHeader('Content-Security-Policy', policy)
    }

    next()
  }

  return {
    name: 'knowvia-frame-ancestors',
    configureServer(server) {
      server.middlewares.use(middleware)
    },
    configurePreviewServer(server) {
      server.middlewares.use(middleware)
    },
  }
}

export default defineConfig({
  plugins: [react(), tailwindcss(), frameAncestorsPlugin()],
})