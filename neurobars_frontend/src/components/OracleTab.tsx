import { useState } from "react"
import ReactMarkdown from "react-markdown"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
} from "@/components/ui/card"

interface SearchResult {
  artist: string
  title: string
  score?: number | null
}

export function OracleTab() {
  const [query, setQuery] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [results, setResults] = useState<SearchResult[]>([])
  const [answer, setAnswer] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    if (!query.trim()) return
    
    setIsLoading(true)
    setError(null)
    setResults([])
    setAnswer(null)

    try {
      const params = new URLSearchParams({
        query,
        limit: "9"
      })
      const res = await fetch(`http://localhost:8000/api/search-and-process?${params.toString()}`)

      if (!res.ok) throw new Error(`API error ${res.status}`)

      const body = await res.json()
      
      setAnswer(body.answer || body.generated_text || "No insights generated.")

      const items = body.results || body.sources || []
      const normalized = items.map((it: any) => ({
        title: it.title ?? it.metadata?.title ?? "Unknown Title",
        artist: it.artist ?? it.metadata?.artist ?? "Unknown Artist",
        score: it.score ?? it.similarity ?? it.points ?? null,
      }))

      setResults(normalized)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch data.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="max-w-5xl mx-auto w-full space-y-8">
      <div className="flex items-center gap-4">
        <Input
          placeholder="Ask the Oracle about lyrics, themes, or artists..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          className="bg-zinc-900/60 border-white/10 text-zinc-100 h-12"
        />
        <Button onClick={handleSearch} disabled={isLoading} className="bg-purple-600 hover:bg-purple-700 h-12 px-8">
          {isLoading ? "Searching..." : "Search"}
        </Button>
      </div>

      {error && (
        <div className="p-4 rounded-md bg-red-900/20 border border-red-900/50 text-red-400">
          {error}
        </div>
      )}

      {isLoading && (
        <div className="space-y-4">
          <Skeleton className="h-32 w-full bg-zinc-800" />
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Skeleton className="h-24 bg-zinc-800" />
            <Skeleton className="h-24 bg-zinc-800" />
            <Skeleton className="h-24 bg-zinc-800" />
          </div>
        </div>
      )}

      {answer && !isLoading && (
        <Card className="bg-zinc-900/60 border-purple-500/30">
          <CardHeader>
            <CardTitle className="text-purple-400 text-xs uppercase tracking-widest">Oracle's Insight</CardTitle>
          </CardHeader>
          <CardContent className="text-zinc-100 leading-relaxed prose prose-invert max-w-none">
            <ReactMarkdown>{answer}</ReactMarkdown>
          </CardContent>
        </Card>
      )}

      {!isLoading && results.length > 0 && (
        <div className="space-y-4">
          <h3 className="text-sm font-semibold text-zinc-500 uppercase tracking-wider">Citations</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {results.map((r, idx) => (
              <Card key={idx} className="p-4 bg-zinc-900 border border-white/5">
                <CardTitle className="text-sm font-bold text-zinc-100">{r.title}</CardTitle>
                <div className="text-[11px] text-zinc-500 mt-0.5">{r.artist}</div>
                <div className="mt-3 flex justify-between items-center">
                  <span className="text-[9px] text-zinc-700 uppercase">Source</span>
                  {r.score && <span className="text-[10px] font-mono text-zinc-600">Sim: {r.score.toFixed(3)}</span>}
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}