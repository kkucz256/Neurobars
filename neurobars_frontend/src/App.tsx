import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { StudioTab } from "@/components/studiotab"
import { OracleTab } from "@/components/OracleTab"

function App() {
  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-zinc-900 via-zinc-950 to-black text-zinc-50 font-sans selection:bg-purple-900/50">
      <header className="border-b border-white/5 bg-black/20 backdrop-blur-md py-6 sticky top-0 z-10">
        <div className="container mx-auto px-4 max-w-5xl">
          <h1 className="text-3xl font-bold tracking-tighter text-white">
            NEURO<span className="text-purple-500">BARS</span>
          </h1>
        </div>
      </header>

      <main className="container mx-auto px-4 max-w-5xl py-12">
        <Tabs defaultValue="studio" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-8 bg-zinc-900/40 border border-white/5 p-1 rounded-lg">
            <TabsTrigger 
              value="oracle" 
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-zinc-400"
            >
              The Oracle
            </TabsTrigger>
            <TabsTrigger 
              value="studio" 
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-zinc-400"
            >
              The Studio
            </TabsTrigger>
            <TabsTrigger 
              value="booth" 
              className="data-[state=active]:bg-purple-600 data-[state=active]:text-white text-zinc-400"
            >
              The Booth
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="oracle" className="min-h-[500px] border border-white/5 rounded-xl p-8 bg-black/40 shadow-2xl backdrop-blur-sm">
            <OracleTab />
          </TabsContent>
          
          <TabsContent value="studio" className="min-h-[500px] border border-white/5 rounded-xl p-8 bg-black/40 shadow-2xl backdrop-blur-sm">
            <StudioTab />
          </TabsContent>
          
          <TabsContent value="booth" className="min-h-[500px] border border-white/5 rounded-xl p-8 bg-black/40 shadow-2xl backdrop-blur-sm">
            <h2 className="text-2xl font-semibold mb-4 text-zinc-100">Lyrics Quiz</h2>
            <p className="text-sm text-zinc-500">Miejsce na grywalizację (/quiz-game)</p>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

export default App