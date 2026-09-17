"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

/**
 * /discover — V2: the YouTube-based Auto Course Generator has been
 * removed entirely (no more YouTube scraping/content). This route is
 * kept only as a redirect so old links/bookmarks still land somewhere
 * useful — the admin-only Content Manager at /admin, which is now the
 * single place all courses and videos are created or removed.
 */
export default function DiscoverRedirect() {
  const router = useRouter()
  useEffect(() => {
    router.replace("/admin")
  }, [router])
  return null
}
