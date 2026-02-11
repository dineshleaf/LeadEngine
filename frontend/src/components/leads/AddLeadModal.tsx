import { useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { X, Upload, Globe } from 'lucide-react'
import toast from 'react-hot-toast'
import { createLead, createLeadsBulk, uploadCSV } from '../../api/leads'

interface Props {
  onClose: () => void
  onSuccess: () => void
}

export default function AddLeadModal({ onClose, onSuccess }: Props) {
  const [tab, setTab] = useState<'manual' | 'csv'>('manual')
  const [domains, setDomains] = useState('')
  const [loading, setLoading] = useState(false)

  const { getRootProps, getInputProps, isDragActive, acceptedFiles } = useDropzone({
    accept: { 'text/csv': ['.csv'] },
    maxFiles: 1,
  })

  const handleManualSubmit = async () => {
    const domainList = domains
      .split('\n')
      .map((d) => d.trim())
      .filter(Boolean)
    if (domainList.length === 0) {
      toast.error('Enter at least one domain')
      return
    }
    setLoading(true)
    try {
      if (domainList.length === 1) {
        await createLead(domainList[0])
      } else {
        await createLeadsBulk(domainList)
      }
      toast.success(`Added ${domainList.length} lead(s)`)
      onSuccess()
    } catch (err: any) {
      const msg = err?.response?.data?.detail
        || (err?.request ? 'Server not reachable — check deployment' : err?.message || 'Failed to add leads')
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  const handleCSVUpload = async () => {
    if (acceptedFiles.length === 0) {
      toast.error('Select a CSV file first')
      return
    }
    setLoading(true)
    try {
      const result = await uploadCSV(acceptedFiles[0])
      toast.success(`Imported ${result.length} lead(s)`)
      onSuccess()
    } catch (err: any) {
      const msg = err?.response?.data?.detail
        || (err?.request ? 'Server not reachable — check deployment' : err?.message || 'Failed to upload CSV')
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-2xl bg-white shadow-xl">
        <div className="flex items-center justify-between border-b px-6 py-4">
          <h2 className="text-lg font-semibold">Add Leads</h2>
          <button onClick={onClose} className="rounded-lg p-1 hover:bg-gray-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b">
          <button
            onClick={() => setTab('manual')}
            className={`flex-1 py-3 text-sm font-medium ${
              tab === 'manual' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'
            }`}
          >
            <Globe className="mr-2 inline h-4 w-4" />
            Manual Entry
          </button>
          <button
            onClick={() => setTab('csv')}
            className={`flex-1 py-3 text-sm font-medium ${
              tab === 'csv' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'
            }`}
          >
            <Upload className="mr-2 inline h-4 w-4" />
            CSV Upload
          </button>
        </div>

        <div className="p-6">
          {tab === 'manual' ? (
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">
                Enter domains (one per line)
              </label>
              <textarea
                value={domains}
                onChange={(e) => setDomains(e.target.value)}
                placeholder={'example.com\nanother-store.com\nshop.example.org'}
                rows={6}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
              />
              <button
                onClick={handleManualSubmit}
                disabled={loading}
                className="mt-4 w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Adding...' : 'Add Leads'}
              </button>
            </div>
          ) : (
            <div>
              <div
                {...getRootProps()}
                className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition ${
                  isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input {...getInputProps()} />
                <Upload className="mb-3 h-8 w-8 text-gray-400" />
                {acceptedFiles.length > 0 ? (
                  <p className="text-sm font-medium text-gray-700">{acceptedFiles[0].name}</p>
                ) : (
                  <>
                    <p className="text-sm text-gray-500">
                      Drop a CSV file here, or click to select
                    </p>
                    <p className="mt-1 text-xs text-gray-400">
                      CSV should have domains in the first column
                    </p>
                  </>
                )}
              </div>
              <button
                onClick={handleCSVUpload}
                disabled={loading || acceptedFiles.length === 0}
                className="mt-4 w-full rounded-lg bg-blue-600 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Uploading...' : 'Import CSV'}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
