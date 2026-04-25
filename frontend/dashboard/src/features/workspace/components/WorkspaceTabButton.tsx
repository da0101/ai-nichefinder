import { FlaskConical } from 'lucide-react'

import { Button } from '@/components/ui/button'

interface WorkspaceTabButtonProps {
  active: boolean
  icon: typeof FlaskConical
  title: string
  description: string
  onClick: () => void
}

export function WorkspaceTabButton({
  active,
  icon: Icon,
  title,
  description,
  onClick,
}: WorkspaceTabButtonProps) {
  return (
    <Button
      type="button"
      variant={active ? 'default' : 'outline'}
      className="h-auto min-w-[210px] justify-start rounded-xl px-4 py-3 text-left"
      onClick={onClick}
    >
      <Icon className="mt-0.5 h-4 w-4 shrink-0" />
      <span className="flex min-w-0 flex-col">
        <span className="text-sm font-semibold">{title}</span>
        <span className={`text-xs ${active ? 'text-blue-100' : 'text-slate-500'}`}>{description}</span>
      </span>
    </Button>
  )
}
