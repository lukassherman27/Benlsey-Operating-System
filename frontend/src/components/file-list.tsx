"use client"

import * as React from "react"
import { useState, useEffect } from "react"
import { File, Download, Trash2, Loader2, Folder } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface FileListProps {
  projectCode: string
  category?: string
  className?: string
}

interface UploadedFile {
  file_id: number
  filename: string
  category: string
  file_type: string
  file_size: number
  uploaded_by: string
  created_at: string
}

export function FileList({ projectCode, category, className }: FileListProps) {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [loading, setLoading] = useState(true)

  const fetchFiles = async () => {
    setLoading(true)
    try {
      const url = new URL(`${API_BASE}/api/files/by-project/${encodeURIComponent(projectCode)}`)
      if (category) url.searchParams.set("category", category)
      const res = await fetch(url.toString())
      if (res.ok) {
        const data = await res.json()
        setFiles(data.files || [])
      }
    } catch (e) {
      console.error("Failed to fetch files:", e)
    }
    setLoading(false)
  }

  useEffect(() => { fetchFiles() }, [projectCode, category])

  const handleDownload = async (fileId: number) => {
    try {
      const res = await fetch(`${API_BASE}/api/files/download/${fileId}`)
      if (res.ok) {
        const data = await res.json()
        if (data.download_url) window.open(data.download_url, "_blank")
      }
    } catch (e) {
      console.error("Download failed:", e)
    }
  }

  const handleDelete = async (fileId: number) => {
    if (!confirm("Delete this file?")) return
    try {
      const res = await fetch(`${API_BASE}/api/files/uploaded/${fileId}`, { method: "DELETE" })
      if (res.ok) setFiles(files.filter(f => f.file_id !== fileId))
    } catch (e) {
      console.error("Delete failed:", e)
    }
  }

  const formatSize = (bytes: number) => {
    if (!bytes) return "-"
    const k = 1024
    const sizes = ["B", "KB", "MB", "GB"]
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
  }

  if (loading) return <div className="flex justify-center py-8"><Loader2 className="h-6 w-6 animate-spin" /></div>
  if (files.length === 0) return <div className="text-center py-8 text-muted-foreground"><Folder className="mx-auto h-12 w-12 mb-2 opacity-50" /><p>No files uploaded</p></div>

  return (
    <div className={cn("", className)}>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Size</TableHead>
            <TableHead>By</TableHead>
            <TableHead>Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {files.map(f => (
            <TableRow key={f.file_id}>
              <TableCell><div className="flex items-center gap-2"><File className="h-4 w-4" />{f.filename}</div></TableCell>
              <TableCell><Badge variant="secondary">{f.category}</Badge></TableCell>
              <TableCell>{formatSize(f.file_size)}</TableCell>
              <TableCell>{f.uploaded_by || "-"}</TableCell>
              <TableCell>
                <div className="flex gap-1">
                  <Button variant="ghost" size="sm" onClick={() => handleDownload(f.file_id)}><Download className="h-4 w-4" /></Button>
                  <Button variant="ghost" size="sm" className="text-red-500" onClick={() => handleDelete(f.file_id)}><Trash2 className="h-4 w-4" /></Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
