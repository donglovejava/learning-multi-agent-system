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

async function postJSON<T>(path: string, body: any): Promise<T> {
  const resp = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
    },
    body: JSON.stringify(body),
  })
  if (!resp.ok) {
    const errText = await resp.text().catch(() => '')
    throw new Error(`HTTP ${resp.status}: ${errText}`)
  }
  return resp.json()
}

export async function chat(req: ChatRequest): Promise<ChatResponse> {
  return postJSON<ChatResponse>('/chat', req)
}

export async function generateResources(req: ResourceRequest): Promise<ResourceResponse> {
  return postJSON<ResourceResponse>('/resources', req)
}
