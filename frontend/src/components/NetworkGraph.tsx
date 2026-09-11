import React, { useRef, useEffect, useState } from 'react'
import { ZoomIn, ZoomOut, RotateCcw, ShieldAlert, Store, User, CreditCard } from 'lucide-react'

export interface GraphNode {
  id: string
  label: string
  type: 'SETTLEMENT_ACCOUNT' | 'MERCHANT' | 'CUSTOMER'
  category?: string
  kyc_status?: string
  risk_score: number
  size: number
  color: string
  x?: number
  y?: number
  vx?: number
  vy?: number
}

export interface GraphEdge {
  source: string
  target: string
  label?: string
  amount?: number
  status?: string
  color: string
}

interface NetworkGraphProps {
  nodes: GraphNode[]
  edges: GraphEdge[]
  onNodeClick?: (node: GraphNode) => void
  selectedNodeId?: string | null
}

export const NetworkGraph: React.FC<NetworkGraphProps> = ({
  nodes: initialNodes,
  edges: initialEdges,
  onNodeClick,
  selectedNodeId
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const [nodes, setNodes] = useState<GraphNode[]>([])
  const [edges, setEdges] = useState<GraphEdge[]>([])
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1.0 })
  const [draggedNode, setDraggedNode] = useState<GraphNode | null>(null)
  const [isPanning, setIsPanning] = useState(false)
  const [panStart, setPanStart] = useState({ x: 0, y: 0 })
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)

  // Initialize nodes with layout
  useEffect(() => {
    if (!initialNodes || initialNodes.length === 0) return

    const width = 800
    const height = 500
    const centerX = width / 2
    const centerY = height / 2

    // Layout: Anchor/Account at center, Merchants in inner circle, Customers in outer circle
    const laidOutNodes: GraphNode[] = initialNodes.map((node, i) => {
      let x = centerX
      let y = centerY

      if (node.type === 'SETTLEMENT_ACCOUNT') {
        x = centerX
        y = centerY
      } else if (node.type === 'MERCHANT') {
        const angle = (i * 2 * Math.PI) / Math.max(1, initialNodes.filter(n => n.type === 'MERCHANT').length)
        const radius = 140 + (i % 2) * 30
        x = centerX + radius * Math.cos(angle)
        y = centerY + radius * Math.sin(angle)
      } else {
        // Customer
        const angle = (i * 2 * Math.PI) / Math.max(1, initialNodes.filter(n => n.type === 'CUSTOMER').length)
        const radius = 240 + (i % 3) * 40
        x = centerX + radius * Math.cos(angle)
        y = centerY + radius * Math.sin(angle)
      }

      return {
        ...node,
        x: node.x ?? x,
        y: node.y ?? y,
        vx: 0,
        vy: 0
      }
    })

    setNodes(laidOutNodes)
    setEdges(initialEdges || [])
    setTransform({ x: 0, y: 0, scale: 0.9 })
  }, [initialNodes, initialEdges])

  // Canvas render loop
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId: number

    const render = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      ctx.save()
      ctx.translate(transform.x, transform.y)
      ctx.scale(transform.scale, transform.scale)

      const nodeMap = new Map<string, GraphNode>()
      nodes.forEach(n => nodeMap.set(n.id, n))

      // 1. Draw Edges
      edges.forEach(edge => {
        const src = nodeMap.get(edge.source)
        const tgt = nodeMap.get(edge.target)
        if (!src || !tgt || src.x === undefined || src.y === undefined || tgt.x === undefined || tgt.y === undefined) return

        const isHighlighted = selectedNodeId && (edge.source === selectedNodeId || edge.target === selectedNodeId)

        ctx.beginPath()
        ctx.moveTo(src.x, src.y)
        ctx.lineTo(tgt.x, tgt.y)
        ctx.strokeStyle = isHighlighted ? '#3b82f6' : (edge.color || '#334155')
        ctx.lineWidth = isHighlighted ? 2.5 : 1.2
        ctx.stroke()

        // Edge label (Amount / Status)
        if (edge.label && transform.scale > 0.7) {
          const midX = (src.x + tgt.x) / 2
          const midY = (src.y + tgt.y) / 2
          ctx.fillStyle = '#94a3b8'
          ctx.font = '9px JetBrains Mono'
          ctx.fillText(edge.label, midX + 3, midY - 3)
        }
      })

      // 2. Draw Nodes
      nodes.forEach(node => {
        if (node.x === undefined || node.y === undefined) return

        const isSelected = selectedNodeId === node.id
        const isHovered = hoveredNode?.id === node.id

        // Glow ring for high risk or selection
        if (isSelected || isHovered || node.risk_score >= 80) {
          ctx.beginPath()
          ctx.arc(node.x, node.y, node.size / 2 + 5, 0, 2 * Math.PI)
          ctx.fillStyle = isSelected ? 'rgba(59, 130, 246, 0.4)' : node.color + '44'
          ctx.fill()
        }

        // Main node circle
        ctx.beginPath()
        ctx.arc(node.x, node.y, node.size / 2, 0, 2 * Math.PI)
        ctx.fillStyle = node.color
        ctx.fill()
        ctx.strokeStyle = isSelected ? '#ffffff' : '#1e293b'
        ctx.lineWidth = isSelected ? 3 : 1.5
        ctx.stroke()

        // Node text label
        ctx.fillStyle = '#f8fafc'
        ctx.font = isSelected ? 'bold 11px Plus Jakarta Sans' : '10px Plus Jakarta Sans'
        ctx.textAlign = 'center'
        ctx.fillText(node.label, node.x, node.y + node.size / 2 + 12)
      })

      ctx.restore()
    }

    render()
  }, [nodes, edges, transform, selectedNodeId, hoveredNode])

  // Mouse event handlers for interaction
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    const mouseX = (e.clientX - rect.left - transform.x) / transform.scale
    const mouseY = (e.clientY - rect.top - transform.y) / transform.scale

    // Check if clicked a node
    const clicked = nodes.find(n => {
      if (n.x === undefined || n.y === undefined) return false
      const dist = Math.hypot(n.x - mouseX, n.y - mouseY)
      return dist <= n.size / 2 + 4
    })

    if (clicked) {
      setDraggedNode(clicked)
      if (onNodeClick) onNodeClick(clicked)
    } else {
      setIsPanning(true)
      setPanStart({ x: e.clientX - transform.x, y: e.clientY - transform.y })
    }
  }

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas) return
    const rect = canvas.getBoundingClientRect()
    const mouseX = (e.clientX - rect.left - transform.x) / transform.scale
    const mouseY = (e.clientY - rect.top - transform.y) / transform.scale

    if (draggedNode) {
      setNodes(prev => prev.map(n => n.id === draggedNode.id ? { ...n, x: mouseX, y: mouseY } : n))
    } else if (isPanning) {
      setTransform(prev => ({
        ...prev,
        x: e.clientX - panStart.x,
        y: e.clientY - panStart.y
      }))
    } else {
      const hovered = nodes.find(n => {
        if (n.x === undefined || n.y === undefined) return false
        const dist = Math.hypot(n.x - mouseX, n.y - mouseY)
        return dist <= n.size / 2 + 4
      })
      setHoveredNode(hovered || null)
    }
  }

  const handleMouseUp = () => {
    setDraggedNode(null)
    setIsPanning(false)
  }

  const handleWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault()
    const zoomFactor = e.deltaY < 0 ? 1.1 : 0.9
    setTransform(prev => ({
      ...prev,
      scale: Math.max(0.3, Math.min(2.5, prev.scale * zoomFactor))
    }))
  }

  const handleReset = () => {
    setTransform({ x: 0, y: 0, scale: 0.9 })
  }

  return (
    <div className="relative w-full h-[520px] rounded-2xl border border-[#222f4c] bg-[#0c101a] overflow-hidden">
      {/* Canvas */}
      <canvas
        ref={canvasRef}
        width={900}
        height={520}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onWheel={handleWheel}
        className="cursor-grab active:cursor-grabbing w-full h-full"
      />

      {/* Control Buttons */}
      <div className="absolute top-4 right-4 flex items-center gap-1.5 rounded-xl border border-[#222f4c] bg-[#111726]/90 p-1 backdrop-blur-md">
        <button
          onClick={() => setTransform(prev => ({ ...prev, scale: Math.min(2.5, prev.scale * 1.2) }))}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-[#161f33] hover:text-white transition-colors"
          title="Zoom In"
        >
          <ZoomIn className="h-4 w-4" />
        </button>
        <button
          onClick={() => setTransform(prev => ({ ...prev, scale: Math.max(0.3, prev.scale * 0.8) }))}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-[#161f33] hover:text-white transition-colors"
          title="Zoom Out"
        >
          <ZoomOut className="h-4 w-4" />
        </button>
        <button
          onClick={handleReset}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-[#161f33] hover:text-white transition-colors"
          title="Reset View"
        >
          <RotateCcw className="h-4 w-4" />
        </button>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 flex items-center gap-4 rounded-xl border border-[#222f4c] bg-[#111726]/90 px-3.5 py-2 backdrop-blur-md text-xs">
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full bg-red-500"></span>
          <span className="text-slate-300">Settlement Account</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full bg-purple-500"></span>
          <span className="text-slate-300">Merchant</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-3 w-3 rounded-full bg-blue-500"></span>
          <span className="text-slate-300">Customer</span>
        </div>
      </div>
    </div>
  )
}
