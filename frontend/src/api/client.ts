const API_BASE = '/api/v1'

export interface ChatRequest {
  student_id: string
  message: string
  conversation_id?: string
}

export interface ChatResponse {
  reply: string
  profile_updated: boolean
  explanation?: string
  conversation_id: string
}

export interface ResourceRequest {
  student_id: string
  knowledge_point: string
  resource_types?: string[]
  scaffold_level?: string
}

export interface ResourceResponse {
  resources: Array<{
    type: string
    content: any
    [key: string]: any
  }>
  generation_time: number
  scaffold_level: string
  explanations: string[]
}

export async function chat(req: ChatRequest): Promise<ChatResponse> {
  const resp = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  return resp.json()
}

export async function generateResources(req: ResourceRequest): Promise<ResourceResponse> {
  const resp = await fetch(`${API_BASE}/resources`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
  return resp.json()
}
