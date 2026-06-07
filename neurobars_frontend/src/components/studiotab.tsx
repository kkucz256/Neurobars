import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { Skeleton } from "@/components/ui/skeleton"

interface Reference {
  points: number
  artist: string
  title: string
  lyrics: string
}

interface GeneratedResult {
  artist: string
  topic: string
  generated_lyrics: string
  used_references: Reference[]
}

export function StudioTab() {
  const [artists, setArtists] = useState<string[]>([])
  const [selectedArtist, setSelectedArtist] = useState<string>("")
  const [topic, setTopic] = useState("")
  const [comboboxOpen, setComboboxOpen] = useState(false)
  
  const [isGenerating, setIsGenerating] = useState(false)
  const [result, setResult] = useState<GeneratedResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  // 1. Initialization: Fetch artists from Django
  useEffect(() => {
    fetch("http://localhost:8000/api/artists")
      .then((res) => {
        if (!res.ok) throw new Error("Failed to fetch artists")
        return res.json()
      })
      .then((data) => setArtists(data))
      .catch((err) => {
        console.error(err)
        setError("Failed to fetch artists database. Verify if backend and CORS are running.")
      })
  }, [])

  // 2. Action: Hit the generator endpoint
  const handleGenerate = async () => {
    if (!selectedArtist || !topic) return

    setIsGenerating(true)
    setError(null)
    setResult(null)

    try {
      const params = new URLSearchParams({
        artist: selectedArtist,
        topic: topic
      })

      const response = await fetch(`http://localhost:8000/api/generate-bars?${params.toString()}`)
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data: GeneratedResult = await response.json()
      setResult(data)
    } catch (err) {
      console.error(err)
      setError("LLM model or Vector DB returned an error. Check Django container logs.")
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="space-y-8">
      {/* Control Panel: intent = wider (2 columns), right column stacked: artist above generate */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-start">
        <div className="md:col-span-2">
          <Input
            placeholder="Enter a topic (e.g. driving at night, losing a friend)..."
            value={topic}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setTopic(e.target.value)}
            className="w-full h-24 bg-zinc-900/50 border-white/10 text-zinc-100 focus-visible:ring-purple-500"
          />
        </div>

        <div className="flex flex-col gap-3">
          <Popover open={comboboxOpen} onOpenChange={setComboboxOpen}>
            <PopoverTrigger asChild>
              <Button
                variant="outline"
                role="combobox"
                aria-expanded={comboboxOpen}
                className="w-full justify-between bg-zinc-900/50 border-white/10 text-zinc-100 hover:bg-zinc-800 h-12"
              >
                {selectedArtist || "Select an artist..."}
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-full p-0 bg-zinc-900 border-white/10 text-white">
              <Command className="bg-transparent">
                <CommandInput placeholder="Search artist..." className="text-zinc-100" />
                <CommandList>
                  <CommandEmpty>No artist found in DB.</CommandEmpty>
                  <CommandGroup>
                    {artists.map((artist) => (
                      <CommandItem
                        key={artist}
                        value={artist}
                        onSelect={(currentValue: string) => {
                          setSelectedArtist(currentValue === selectedArtist ? "" : currentValue)
                          setComboboxOpen(false)
                        }}
                        className="text-zinc-200 cursor-pointer hover:bg-purple-900/50 data-[selected=true]:bg-purple-900/80"
                      >
                        {artist}
                      </CommandItem>
                    ))}
                  </CommandGroup>
                </CommandList>
              </Command>
            </PopoverContent>
          </Popover>

          <Button
            onClick={handleGenerate}
            disabled={!selectedArtist || !topic || isGenerating}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white font-semibold transition-all disabled:opacity-50 h-12"
          >
            {isGenerating ? "Cooking bars..." : "Generate Bars"}
          </Button>
        </div>
      </div>

      {/* Error Handling */}
      {error && (
        <div className="p-4 rounded-md bg-red-900/20 border border-red-900/50 text-red-400">
          {error}
        </div>
      )}

      {/* Loader */}
      {isGenerating && (
        <div className="space-y-4 animate-pulse">
          <Skeleton className="h-4 w-1/3 bg-zinc-800" />
          <Skeleton className="h-32 w-full bg-zinc-800" />
          <Skeleton className="h-4 w-1/4 bg-zinc-800" />
        </div>
      )}

      {/* Result */}
      {result && !isGenerating && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="p-6 rounded-xl bg-zinc-900/40 border border-white/10">
            <h3 className="text-xl font-bold text-white mb-4">
              <span className="text-purple-500">{result.artist}</span> type bars about <span className="italic text-zinc-400">"{result.topic}"</span>
            </h3>
            <pre className="whitespace-pre-wrap font-sans text-lg text-zinc-200 leading-relaxed">
              {result.generated_lyrics}
            </pre>
          </div>

          <div className="p-6 rounded-xl bg-black/40 border border-white/5">
            <h4 className="text-sm font-bold text-zinc-500 uppercase tracking-wider mb-4">Under the hood (RAG References)</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {result.used_references.slice(0, 4).map((ref, i) => (
                <div key={i} className="p-3 rounded-lg bg-zinc-900/30 border border-white/5 text-xs">
                  <span className="block font-bold text-zinc-300 mb-1">{ref.title}</span>
                  <span className="text-zinc-500 line-clamp-2">{ref.lyrics}</span>
                  <span className="block mt-2 text-purple-900/80 font-mono">Sim: {ref.points.toFixed(3)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}