import { Menu, BarChart3 } from 'lucide-react'

export default function MobileNav({ onMenuClick }: { onMenuClick: () => void }) {
  return (
    <nav className="md:hidden fixed top-0 left-0 right-0 z-30 bg-slate-900/95 border-b border-slate-800 backdrop-blur-sm">
      <div className="flex items-center justify-between px-4 h-14">
        <button onClick={onMenuClick} className="text-slate-400 hover:text-white">
          <Menu className="w-6 h-6" />
        </button>
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary-400" />
          <span className="font-semibold text-sm text-white">Contabilidad BI</span>
        </div>
        <div className="w-6" />
      </div>
    </nav>
  )
}
