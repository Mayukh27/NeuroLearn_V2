"use client"

import { useState, useEffect, useCallback } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  Settings,
  Plus,
  Trash2,
  Link2,
  Unlink,
  Film,
  BookOpen,
  KeyRound,
  AlertCircle,
  CheckCircle2,
} from "lucide-react"

import {
  getAdminKey,
  setAdminKey,
  clearAdminKey,
  AdminAuthError,
  adminListCourses,
  adminCreateCourse,
  adminDeleteCourse,
  adminListVideos,
  adminRegisterVideo,
  adminDeleteVideo,
  adminAttachVideo,
  adminAttachYoutubeVideo,
  adminDetachVideo,
  type AdminCourse,
  type AdminLocalVideo,
} from "@/lib/adminApi"

/**
 * /admin — Content Manager (V2, Phase 4)
 *
 * V2 removes all YouTube content and every hardcoded/student-pasted
 * video URL. Every course and every video in the catalog is created and
 * removed here, by whoever holds the admin key — nowhere else.
 */
export default function AdminPage() {
  const [keyInput, setKeyInput] = useState("")
  const [unlocked, setUnlocked] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const [courses, setCourses] = useState<AdminCourse[]>([])
  const [videos, setVideos] = useState<AdminLocalVideo[]>([])
  const [loading, setLoading] = useState(false)

  const [newCourseTitle, setNewCourseTitle] = useState("")
  const [newCourseCategory, setNewCourseCategory] = useState("")
  const [newVideoTitle, setNewVideoTitle] = useState("")
  const [newVideoPath, setNewVideoPath] = useState("")
  const [attachChoice, setAttachChoice] = useState<Record<string, string>>({})
  const [attachSource, setAttachSource] = useState<Record<string, "local" | "youtube">>({})
  const [ytTitle, setYtTitle] = useState<Record<string, string>>({})
  const [ytUrl, setYtUrl] = useState<Record<string, string>>({})

  const flash = (msg: string) => {
    setNotice(msg)
    setTimeout(() => setNotice(null), 3000)
  }

  const handleAuthError = (e: unknown) => {
    if (e instanceof AdminAuthError) {
      setUnlocked(false)
      clearAdminKey()
      setError("Admin key rejected — enter it again.")
      return true
    }
    setError(e instanceof Error ? e.message : String(e))
    return false
  }

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [c, v] = await Promise.all([adminListCourses(), adminListVideos()])
      setCourses(c)
      setVideos(v)
    } catch (e) {
      handleAuthError(e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const existing = getAdminKey()
    if (existing) {
      setUnlocked(true)
      refresh()
    }
  }, [refresh])

  const handleUnlock = async () => {
    if (!keyInput.trim()) return
    setAdminKey(keyInput.trim())
    setUnlocked(true)
    setError(null)
    await refresh()
  }

  const handleLock = () => {
    clearAdminKey()
    setUnlocked(false)
    setKeyInput("")
  }

  const handleCreateCourse = async () => {
    if (!newCourseTitle.trim()) return
    try {
      await adminCreateCourse({
        title: newCourseTitle.trim(),
        category: newCourseCategory.trim() || "General",
      })
      setNewCourseTitle("")
      setNewCourseCategory("")
      flash("Course created")
      await refresh()
    } catch (e) {
      handleAuthError(e)
    }
  }

  const handleDeleteCourse = async (courseId: string) => {
    try {
      await adminDeleteCourse(courseId)
      flash("Course deleted")
      await refresh()
    } catch (e) {
      handleAuthError(e)
    }
  }

  const handleRegisterVideo = async () => {
    if (!newVideoTitle.trim() || !newVideoPath.trim()) return
    try {
      await adminRegisterVideo({ title: newVideoTitle.trim(), relative_path: newVideoPath.trim() })
      setNewVideoTitle("")
      setNewVideoPath("")
      flash("Video registered")
      await refresh()
    } catch (e) {
      handleAuthError(e)
    }
  }

  const handleDeleteVideo = async (id: string) => {
    try {
      await adminDeleteVideo(id)
      flash("Video removed from library")
      await refresh()
    } catch (e) {
      handleAuthError(e)
    }
  }

  const handleAttach = async (courseId: string) => {
    const localVideoId = attachChoice[courseId]
    if (!localVideoId) return
    try {
      await adminAttachVideo(courseId, localVideoId)
      flash("Video attached to course")
      await refresh()
    } catch (e) {
      handleAuthError(e)
    }
  }

  const handleAttachYoutube = async (courseId: string) => {
    const title = (ytTitle[courseId] || "").trim()
    const url = (ytUrl[courseId] || "").trim()
    if (!title || !url) return
    try {
      await adminAttachYoutubeVideo(courseId, { title, youtube_url: url })
      setYtTitle((prev) => ({ ...prev, [courseId]: "" }))
      setYtUrl((prev) => ({ ...prev, [courseId]: "" }))
      flash("YouTube video attached to course")
      await refresh()
    } catch (e) {
      handleAuthError(e)
    }
  }

  const handleDetach = async (courseId: string, videoLinkId: string) => {
    try {
      await adminDetachVideo(courseId, videoLinkId)
      flash("Video detached from course")
      await refresh()
    } catch (e) {
      handleAuthError(e)
    }
  }

  const unattachedVideos = (courseId: string) => {
    const attachedIds = new Set(
      (courses.find((c) => c.id === courseId)?.video_links || []).map((v) => v.local_video_id)
    )
    return videos.filter((v) => !attachedIds.has(v.id))
  }

  // ── Locked state: ask for the admin key ──
  if (!unlocked) {
    return (
      <div className="p-6 max-w-md mx-auto mt-20">
        <div className="rounded-2xl bg-[var(--bg-card)] border border-[var(--border-subtle)] p-6 space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/30 to-purple-600/30 border border-violet-500/20 flex items-center justify-center">
              <KeyRound size={18} className="text-violet-400" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-[var(--text-primary)]">Admin Access</h1>
              <p className="text-xs text-[var(--text-muted)]">Content management is gated by the server's admin key.</p>
            </div>
          </div>
          <input
            type="password"
            value={keyInput}
            onChange={(e) => setKeyInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleUnlock()}
            placeholder="Admin key"
            className="w-full px-4 py-2.5 text-sm rounded-xl bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-violet-500/50"
          />
          {error && (
            <p className="text-xs text-red-400 flex items-center gap-1.5"><AlertCircle size={13} /> {error}</p>
          )}
          <button
            onClick={handleUnlock}
            disabled={!keyInput.trim()}
            className="w-full px-4 py-2.5 text-sm font-semibold rounded-xl bg-gradient-to-r from-violet-500 to-purple-600 text-white disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Unlock
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-[900px] mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500/30 to-purple-600/30 border border-violet-500/20 flex items-center justify-center">
            <Settings size={20} className="text-violet-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">Content Manager</h1>
            <p className="text-sm text-[var(--text-muted)]">
              All courses and videos come from here — no YouTube, no ad-hoc URLs.
            </p>
          </div>
        </div>
        <button
          onClick={handleLock}
          className="text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
        >
          Lock
        </button>
      </div>

      <AnimatePresence>
        {notice && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-green-500/10 border border-green-500/20 text-green-400 text-sm"
          >
            <CheckCircle2 size={15} /> {notice}
          </motion.div>
        )}
      </AnimatePresence>
      {error && (
        <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          <AlertCircle size={15} /> {error}
        </div>
      )}

      {/* Local video library */}
      <section className="rounded-2xl bg-[var(--bg-card)] border border-[var(--border-subtle)] p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Film size={16} className="text-violet-400" />
          <h2 className="text-sm font-bold text-[var(--text-primary)]">Video Library</h2>
          <span className="text-xs text-[var(--text-muted)]">({videos.length})</span>
        </div>
        <p className="text-xs text-[var(--text-muted)]">
          Register a video file already placed on the server under <code>VIDEO_STORAGE_DIR</code> — this does not upload anything.
        </p>
        <div className="flex flex-wrap gap-2">
          <input
            value={newVideoTitle}
            onChange={(e) => setNewVideoTitle(e.target.value)}
            placeholder="Title"
            className="flex-1 min-w-[160px] px-3 py-2 text-sm rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-violet-500/50"
          />
          <input
            value={newVideoPath}
            onChange={(e) => setNewVideoPath(e.target.value)}
            placeholder="relative/path/lecture-01.mp4"
            className="flex-1 min-w-[220px] px-3 py-2 text-sm rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-violet-500/50"
          />
          <button
            onClick={handleRegisterVideo}
            disabled={!newVideoTitle.trim() || !newVideoPath.trim()}
            className="px-3 py-2 text-sm font-semibold rounded-lg bg-violet-500/20 border border-violet-500/30 text-violet-300 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            <Plus size={14} /> Register
          </button>
        </div>
        <div className="space-y-1.5">
          {videos.map((v) => (
            <div key={v.id} className="flex items-center justify-between px-3 py-2 rounded-lg bg-[var(--bg-elevated)] text-sm">
              <div className="min-w-0">
                <p className="text-[var(--text-primary)] truncate">{v.title}</p>
                <p className="text-[10px] font-mono text-[var(--text-muted)] truncate">{v.relative_path}</p>
              </div>
              <button onClick={() => handleDeleteVideo(v.id)} className="shrink-0 text-[var(--text-muted)] hover:text-red-400 transition-colors p-1">
                <Trash2 size={14} />
              </button>
            </div>
          ))}
          {videos.length === 0 && !loading && (
            <p className="text-xs text-[var(--text-muted)] italic">No videos registered yet.</p>
          )}
        </div>
      </section>

      {/* Courses */}
      <section className="rounded-2xl bg-[var(--bg-card)] border border-[var(--border-subtle)] p-5 space-y-4">
        <div className="flex items-center gap-2">
          <BookOpen size={16} className="text-violet-400" />
          <h2 className="text-sm font-bold text-[var(--text-primary)]">Courses</h2>
          <span className="text-xs text-[var(--text-muted)]">({courses.length})</span>
        </div>
        <div className="flex flex-wrap gap-2">
          <input
            value={newCourseTitle}
            onChange={(e) => setNewCourseTitle(e.target.value)}
            placeholder="Course title"
            className="flex-1 min-w-[160px] px-3 py-2 text-sm rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-violet-500/50"
          />
          <input
            value={newCourseCategory}
            onChange={(e) => setNewCourseCategory(e.target.value)}
            placeholder="Category (optional)"
            className="flex-1 min-w-[160px] px-3 py-2 text-sm rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-violet-500/50"
          />
          <button
            onClick={handleCreateCourse}
            disabled={!newCourseTitle.trim()}
            className="px-3 py-2 text-sm font-semibold rounded-lg bg-violet-500/20 border border-violet-500/30 text-violet-300 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            <Plus size={14} /> Create
          </button>
        </div>

        <div className="space-y-3">
          {courses.map((c) => (
            <div key={c.id} className="rounded-xl bg-[var(--bg-elevated)] p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-semibold text-[var(--text-primary)]">{c.title}</p>
                  <p className="text-xs text-[var(--text-muted)]">{c.category} · {c.total_videos} video{c.total_videos === 1 ? "" : "s"}</p>
                </div>
                <button onClick={() => handleDeleteCourse(c.id)} className="text-[var(--text-muted)] hover:text-red-400 transition-colors p-1">
                  <Trash2 size={14} />
                </button>
              </div>

              {c.video_links.length > 0 && (
                <div className="space-y-1">
                  {c.video_links.map((vl) => (
                    <div key={vl.id} className="flex items-center justify-between px-2.5 py-1.5 rounded-lg bg-[var(--bg-card)] text-xs">
                      <span className="text-[var(--text-secondary)] truncate">{vl.title}</span>
                      <button onClick={() => handleDetach(c.id, vl.id)} className="shrink-0 text-[var(--text-muted)] hover:text-amber-400 transition-colors p-1" title="Detach">
                        <Unlink size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex gap-1.5 p-0.5 rounded-lg bg-[var(--bg-card)] w-fit">
                <button
                  onClick={() => setAttachSource((prev) => ({ ...prev, [c.id]: "local" }))}
                  className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-colors ${
                    (attachSource[c.id] || "local") === "local"
                      ? "bg-violet-500/25 text-violet-300"
                      : "text-[var(--text-muted)]"
                  }`}
                >
                  Local
                </button>
                <button
                  onClick={() => setAttachSource((prev) => ({ ...prev, [c.id]: "youtube" }))}
                  className={`px-2.5 py-1 text-[11px] font-semibold rounded-md transition-colors ${
                    attachSource[c.id] === "youtube"
                      ? "bg-violet-500/25 text-violet-300"
                      : "text-[var(--text-muted)]"
                  }`}
                >
                  YouTube
                </button>
              </div>

              {(attachSource[c.id] || "local") === "local" ? (
                <div className="flex gap-2">
                  <select
                    value={attachChoice[c.id] || ""}
                    onChange={(e) => setAttachChoice((prev) => ({ ...prev, [c.id]: e.target.value }))}
                    className="flex-1 px-2.5 py-1.5 text-xs rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)] text-[var(--text-primary)]"
                  >
                    <option value="">Attach a video from the library…</option>
                    {unattachedVideos(c.id).map((v) => (
                      <option key={v.id} value={v.id}>{v.title}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => handleAttach(c.id)}
                    disabled={!attachChoice[c.id]}
                    className="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-violet-500/20 border border-violet-500/30 text-violet-300 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
                  >
                    <Link2 size={12} /> Attach
                  </button>
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  <input
                    value={ytTitle[c.id] || ""}
                    onChange={(e) => setYtTitle((prev) => ({ ...prev, [c.id]: e.target.value }))}
                    placeholder="Video title"
                    className="flex-1 min-w-[120px] px-2.5 py-1.5 text-xs rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
                  />
                  <input
                    value={ytUrl[c.id] || ""}
                    onChange={(e) => setYtUrl((prev) => ({ ...prev, [c.id]: e.target.value }))}
                    placeholder="https://youtube.com/watch?v=…"
                    className="flex-[2] min-w-[180px] px-2.5 py-1.5 text-xs rounded-lg bg-[var(--bg-card)] border border-[var(--border-subtle)] text-[var(--text-primary)] placeholder:text-[var(--text-muted)]"
                  />
                  <button
                    onClick={() => handleAttachYoutube(c.id)}
                    disabled={!(ytTitle[c.id] || "").trim() || !(ytUrl[c.id] || "").trim()}
                    className="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-violet-500/20 border border-violet-500/30 text-violet-300 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
                  >
                    <Link2 size={12} /> Attach
                  </button>
                </div>
              )}
            </div>
          ))}
          {courses.length === 0 && !loading && (
            <p className="text-xs text-[var(--text-muted)] italic">No courses yet — create one above.</p>
          )}
        </div>
      </section>
    </div>
  )
}
