"use client"

import * as React from "react"
import { useState } from "react"
import { Upload, Loader2, CheckCircle, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const CATEGORIES = [
  "Daily Work", "Deliverables", "Client Submissions",
  "Proposals", "Contracts", "Drawings", "Reference"
]

interface FileUploadProps {
  projectCode: string
  onUploadComplete?: (file: { file_id: number; filename: string }) => void
  defaultCategory?: string
  className?: string
}

export function FileUpload({ projectCode, onUploadComplete, defaultCategory = "Daily Work", className }: FileUploadProps) {
  const [category, setCategory] = useState(defaultCategory)
  const [files, setFiles] = useState<File[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadedCount, setUploadedCount] = useState(0)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files))
    }
  }

  const uploadFiles = async () => {
    setUploading(true)
    setUploadedCount(0)

    for (const file of files) {
      const formData = new FormData()
      formData.append("file", file)
      formData.append("project_code", projectCode)
      formData.append("category", category)

      try {
        const res = await fetch(`${API_BASE}/api/files/upload`, { method: "POST", body: formData })
        if (res.ok) {
          const result = await res.json()
          setUploadedCount(c => c + 1)
          onUploadComplete?.(result)
        }
      } catch (e) {
        console.error("Upload failed:", e)
      }
    }

    setUploading(false)
    setFiles([])
  }

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex gap-2">
        <span className="text-sm font-medium">Category:</span>
        <Select value={category} onValueChange={setCategory}>
          <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
          <SelectContent>
            {CATEGORIES.map(c => <SelectItem key={c} value={c}>{c}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div className="border-2 border-dashed rounded-lg p-6 text-center">
        <Upload className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
        <input type="file" multiple onChange={handleFileChange} className="mb-2" />
        {files.length > 0 && (
          <p className="text-sm text-muted-foreground">{files.length} file(s) selected</p>
        )}
      </div>

      {files.length > 0 && (
        <Button onClick={uploadFiles} disabled={uploading}>
          {uploading ? (
            <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Uploading ({uploadedCount}/{files.length})</>
          ) : (
            <><Upload className="mr-2 h-4 w-4" />Upload {files.length} file(s)</>
          )}
        </Button>
      )}
    </div>
  )
}
