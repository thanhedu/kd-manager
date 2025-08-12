import React, { useEffect, useState } from 'react'
import { fetchAccounts } from '../api'
import { decryptJSON } from '../crypto'
import { copyEphemeral } from '../clipboard'

export default function AccountList({ masterKey }) {
  const [list, setList] = useState([])
  const [search, setSearch] = useState('')

  async function load() {
    const rows = await fetchAccounts()
    setList(rows)
  }
  useEffect(() => { load() }, [])

  async function revealField(item, keyPath) {
    // Giải mã tạm thời và copy field vào clipboard (không hiển thị plaintext)
    const obj = await decryptJSON(item, masterKey)
    const val = obj?.[keyPath] || ''
    if (!val) return
    await copyEphemeral(val)
    alert(`Đã copy ${keyPath} vào clipboard (sẽ tự xoá sau vài giây).`)
  }

  const filtered = list.filter(r =>
    (r.title || '').toLowerCase().includes(search.toLowerCase()) ||
    (r.tags || '').toLowerCase().includes(search.toLowerCase())
  )

  return (
    <div className="card list">
      <div style={{display:'flex', gap:12, alignItems:'center'}}>
        <input placeholder="Tìm theo tiêu đề/tags..." value={search} onChange={e=>setSearch(e.target.value)} />
        <button className="ghost" onClick={load}>Tải lại</button>
      </div>
      <div style={{marginTop:12}}>
        {filtered.map(item => (
          <div className="item" key={item.id}>
            <div style={{display:'flex', justifyContent:'space-between'}}>
              <strong>{item.title || 'Untitled'}</strong>
              <div>
                {(item.tags || '').split(',').filter(Boolean).map(t => <span className="badge" key={t.trim()}>{t.trim()}</span>)}
              </div>
            </div>
            <div style={{display:'flex', gap:8, marginTop:8, flexWrap:'wrap'}}>
              <button onClick={()=>revealField(item, 'username')}>Copy Username</button>
              <button onClick={()=>revealField(item, 'email')}>Copy Email</button>
              <button onClick={()=>revealField(item, 'password')}>Copy Password</button>
              <button onClick={()=>revealField(item, 'totp')}>Copy 2FA/TOTP</button>
              <button onClick={()=>revealField(item, 'phone')}>Copy Phone</button>
              <button onClick={()=>revealField(item, 'note')}>Copy Note</button>
            </div>
          </div>
        ))}
        {filtered.length === 0 && <p>Không có bản ghi.</p>}
      </div>
    </div>
  )
}

