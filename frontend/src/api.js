const API_BASE = import.meta.env.VITE_API_BASE

export async function fetchAccounts() {
  const res = await fetch(`${API_BASE}/accounts`)
  if (!res.ok) throw new Error('Fetch failed')
  return await res.json()
}

export async function createAccount(payload) {
  const res = await fetch(`${API_BASE}/accounts`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) throw new Error('Create failed')
  return await res.json()
}

