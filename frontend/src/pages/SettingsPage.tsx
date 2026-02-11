export default function SettingsPage() {
  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Configure API keys and preferences</p>
      </div>

      <div className="max-w-2xl space-y-6">
        <div className="rounded-xl bg-white p-6 border border-gray-200 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">API Keys (Optional)</h2>
          <p className="text-sm text-gray-500 mb-4">
            These keys enhance functionality but are not required for core features.
            Configure them in the <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">.env</code> file in the backend directory.
          </p>

          <div className="space-y-4">
            <div className="rounded-lg border border-gray-200 p-4">
              <h3 className="font-medium text-gray-900 text-sm">SerpAPI Key</h3>
              <p className="text-xs text-gray-500 mt-1">
                Enhanced Google search for auto-discovery. Without this, the free googlesearch-python library is used.
              </p>
            </div>
            <div className="rounded-lg border border-gray-200 p-4">
              <h3 className="font-medium text-gray-900 text-sm">Hunter.io API Key</h3>
              <p className="text-xs text-gray-500 mt-1">
                Professional email finding and verification. Without this, emails are extracted from website content.
              </p>
            </div>
            <div className="rounded-lg border border-gray-200 p-4">
              <h3 className="font-medium text-gray-900 text-sm">Meta Ad Library Token</h3>
              <p className="text-xs text-gray-500 mt-1">
                Access Meta Ad Library API for detailed ad activity. Without this, Facebook Pixel detection is used as a proxy.
              </p>
            </div>
            <div className="rounded-lg border border-gray-200 p-4">
              <h3 className="font-medium text-gray-900 text-sm">OpenAI API Key</h3>
              <p className="text-xs text-gray-500 mt-1">
                LLM-powered pitch generation for more personalized outreach. Without this, template-based pitches are generated.
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-xl bg-white p-6 border border-gray-200 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">Rate Limiting</h2>
          <p className="text-sm text-gray-500">
            The scraper respects rate limits with a default of 2 requests per second per domain.
            Configure <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">REQUESTS_PER_SECOND</code> in
            the <code className="bg-gray-100 px-1.5 py-0.5 rounded text-xs">.env</code> file to adjust.
          </p>
        </div>

        <div className="rounded-xl bg-white p-6 border border-gray-200 shadow-sm">
          <h2 className="text-lg font-semibold mb-4">How to Run</h2>
          <div className="space-y-3 text-sm text-gray-600">
            <div>
              <p className="font-medium text-gray-900 mb-1">Backend:</p>
              <code className="block bg-gray-900 text-green-400 p-3 rounded-lg text-xs">
                cd backend<br />
                pip install -r requirements.txt<br />
                uvicorn app.main:app --reload --port 8000
              </code>
            </div>
            <div>
              <p className="font-medium text-gray-900 mb-1">Frontend:</p>
              <code className="block bg-gray-900 text-green-400 p-3 rounded-lg text-xs">
                cd frontend<br />
                npm install<br />
                npm run dev
              </code>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
